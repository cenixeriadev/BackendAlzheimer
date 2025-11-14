import os
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
import base64
from typing import Dict
from app.utils.config import settings

class StorageService:
    def __init__(self):
        self.is_local = settings.is_local_storage
        self.bucket_name = settings.AWS_BUCKET_NAME
        
        # Configuración base
        s3_config = {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
            'region_name': settings.AWS_REGION
        }
        
        # Config MinIO
        if self.is_local:
            s3_config.update({
                'endpoint_url': settings.AWS_ENDPOINT_URL,
                'verify': False  
            })
            print(f"🔄 Configurando conexión a MinIO local: {settings.AWS_ENDPOINT_URL}")
        else:
            print("🌐 Configurando conexión a AWS S3 real")
        
        self.s3_client = boto3.client('s3', **s3_config)
        self.setup_bucket()
    
    def setup_bucket(self):
        """Crear el bucket si no existe (solo para entorno local)"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket '{self.bucket_name}' ya existe")
        except ClientError:
            if self.is_local:
                try:
                    if settings.AWS_REGION == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                        )
                    print(f"Bucket '{self.bucket_name}' creado exitosamente en MinIO")
                    
                    # Configurar política pública solo para local
                    self._make_bucket_public()
                    
                except ClientError as e:
                    print(f"Error creando bucket: {e}")
                    raise HTTPException(status_code=500, detail=f"Error configurando storage: {e}")
            else:
                # AWS bucket existe
                print(f"Bucket '{self.bucket_name}' no existe en AWS S3")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Bucket '{self.bucket_name}' no existe en AWS S3. Por favor crea el bucket primero."
                )
    
    def _make_bucket_public(self):
        """Hacer el bucket público solo en entorno local"""
        if not self.is_local:
            print("No se configura política pública en AWS S3 real por seguridad")
            return
            
        try:
            public_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=str(public_policy).replace("'", '"')
            )
            print("Política pública configurada en el bucket local")
            
        except Exception as e:
            print(f" No se pudo configurar política pública: {e}")

    async def upload_file(self, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> Dict[str, str]:
        """Subir archivo con configuración apropiada según el entorno"""
        try:
            # Generar nombre único
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"diagnosticos/{uuid.uuid4()}.{file_extension}"
            
            # Configuración de subida según entorno
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': unique_filename,
                'Body': file_content,
                'ContentType': content_type,
                'ACL': 'public-read'
            }
            
            if self.is_local:
                upload_params['ACL'] = 'public-read'
            
            self.s3_client.put_object(**upload_params)
            
            # Generar URL según el entorno
            file_url = await self.get_file_url(unique_filename)
            
            print(f" Archivo subido: {file_url}")
            
            return {
                "filename": unique_filename,
                "url": file_url,
                "message": "Archivo subido exitosamente",
                "environment": "local" if self.is_local else "aws"
            }
            
        except ClientError as e:
            print(f" Error subiendo archivo: {e}")
            raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {e}")

    async def upload_base64_image(self, base64_string: str, filename: str) -> Dict[str, str]:
        """Subir imagen base64"""
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            file_content = base64.b64decode(base64_string)
            content_type = self._get_content_type_from_base64(base64_string)
            
            return await self.upload_file(file_content, filename, content_type)
            
        except Exception as e:
            print(f" Error procesando imagen base64: {e}")
            raise HTTPException(status_code=500, detail=f"Error procesando imagen: {e}")

    def _get_content_type_from_base64(self, base64_string: str) -> str:
        """Determinar tipo de contenido desde base64"""
        if base64_string.startswith('/9j/'):
            return 'image/jpeg'
        elif base64_string.startswith('iVBORw'):
            return 'image/png'
        elif base64_string.startswith('R0lGOD'):
            return 'image/gif'
        elif base64_string.startswith('UklGR'):
            return 'image/webp'
        else:
            return 'image/jpeg'

    async def delete_file(self, filename: str) -> Dict[str, str]:
        """Eliminar archivo"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return {"message": f"Archivo {filename} eliminado exitosamente"}
            
        except ClientError as e:
            print(f" Error eliminando archivo: {e}")
            raise HTTPException(status_code=500, detail=f"Error eliminando archivo: {e}")

    async def get_file_url(self, filename: str) -> str:
        """Obtener URL pública del archivo según el entorno"""
        if self.is_local:
            # URL para MinIO local
            return f"{settings.AWS_ENDPOINT_URL}/{self.bucket_name}/{filename}"
        else:
            # URL para AWS S3 real
            return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"

# Instancia global
storage_service = StorageService()
