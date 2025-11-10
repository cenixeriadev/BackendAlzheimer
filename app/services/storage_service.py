import os
import uuid
import json
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
import base64
from typing import Dict, Optional
from app.config import settings

class StorageService:
    def __init__(self):
        # Configuración base
        s3_config = {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
            'config': boto3.session.Config(signature_version='s3v4')
        }
        
        # Configuración condicional según el entorno
        if settings.AWS_ENDPOINT_URL and settings.AWS_ENDPOINT_URL.strip():
            # Usando MinIO, LocalStack u otro S3-compatible
            s3_config['endpoint_url'] = settings.AWS_ENDPOINT_URL
            
            # Solo deshabilitar SSL en desarrollo local
            if 'localhost' in settings.AWS_ENDPOINT_URL.lower() or '127.0.0.1' in settings.AWS_ENDPOINT_URL:
                s3_config['verify'] = False
        else:
            # Usando AWS S3 real
            s3_config['region_name'] = getattr(settings, 'AWS_REGION', 'us-east-1')
        
        self.s3_client = boto3.client('s3', **s3_config)
        self.bucket_name = settings.AWS_BUCKET_NAME
        self.is_local = bool(settings.AWS_ENDPOINT_URL)
        self.setup_bucket()
    
    def setup_bucket(self):
        """Crear el bucket si no existe"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket '{self.bucket_name}' ya existe")
        except ClientError:
            try:
                # Para AWS real, especificar región en CreateBucket
                if not self.is_local:
                    region = getattr(settings, 'AWS_REGION', 'us-east-1')
                    if region != 'us-east-1':
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': region}
                        )
                    else:
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                
                print(f"Bucket '{self.bucket_name}' creado exitosamente")
                # self._setup_bucket_policy()
                
            except ClientError as e:
                print(f" Error creando bucket: {e}")
                raise HTTPException(status_code=500, detail=f"Error configurando storage: {e}")
    
    # def _setup_bucket_policy(self):
    #     """Configurar política del bucket para permitir acceso público de lectura"""
    #     try:
    #         policy = {
    #             "Version": "2012-10-17",
    #             "Statement": [
    #                 {
    #                     "Effect": "Allow",
    #                     "Principal": "*",
    #                     "Action": ["s3:GetObject"],
    #                     "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
    #                 }
    #             ]
    #         }
    #         self.s3_client.put_bucket_policy(
    #             Bucket=self.bucket_name,
    #             Policy=json.dumps(policy)  # ← Corregido
    #         )
    #         print("Política de bucket configurada")
    #     except Exception as e:
    #         print(f"No se pudo configurar la política del bucket: {e}")

    async def upload_file(self, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> Dict[str, str]:
        """Subir archivo al storage"""
        try:
            # Generar nombre único para el archivo
            file_extension = filename.split('.')[-1] if '.' in filename else 'bin'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Configurar ExtraArgs según el entorno
            extra_args = {'ContentType': content_type}
            if self.is_local:
                extra_args['ACL'] = 'public-read'
            
            # Subir archivo
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_content,
                **extra_args
            )
            
            # Generar URL del archivo
            if self.is_local:
                file_url = f"{settings.AWS_ENDPOINT_URL}/{self.bucket_name}/{unique_filename}"
            else:
                # Para AWS S3 real
                region = getattr(settings, 'AWS_REGION', 'us-east-1')
                file_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"
            
            return {
                "filename": unique_filename,
                "url": file_url,
                "message": "Archivo subido exitosamente"
            }
            
        except ClientError as e:
            print(f"Error subiendo archivo: {e}")
            raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {e}")

    async def upload_base64_image(self, base64_string: str, filename: str) -> Dict[str, str]:
        """Subir imagen en formato base64"""
        try:
            # Decodificar base64
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            file_content = base64.b64decode(base64_string)
            
            # Determinar content type
            content_type = self._get_content_type_from_base64(base64_string)
            
            return await self.upload_file(file_content, filename, content_type)
            
        except Exception as e:
            print(f"Error procesando imagen base64: {e}")
            raise HTTPException(status_code=500, detail=f"Error procesando imagen: {e}")

    def _get_content_type_from_base64(self, base64_string: str) -> str:
        """Determinar el tipo de contenido desde el string base64"""
        signatures = {
            '/9j/': 'image/jpeg',
            'iVBORw': 'image/png',
            'R0lGOD': 'image/gif',
            'UklGR': 'image/webp',
            'Qk': 'image/bmp'
        }
        
        for signature, content_type in signatures.items():
            if base64_string.startswith(signature):
                return content_type
        
        return "application/octet-stream"

    async def delete_file(self, filename: str) -> Dict[str, str]:
        """Eliminar archivo del storage"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return {"message": f"Archivo {filename} eliminado exitosamente"}
            
        except ClientError as e:
            print(f"Error eliminando archivo: {e}")
            raise HTTPException(status_code=500, detail=f"Error eliminando archivo: {e}")

    async def get_file_url(self, filename: str) -> str:
        """Obtener URL del archivo"""
        if self.is_local:
            return f"{settings.AWS_ENDPOINT_URL}/{self.bucket_name}/{filename}"
        else:
            region = getattr(settings, 'AWS_REGION', 'us-east-1')
            return f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{filename}"

    async def list_files(self) -> list:
        """Listar todos los archivos en el bucket"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            files = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'filename': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': await self.get_file_url(obj['Key'])
                    })
            
            return files
            
        except ClientError as e:
            print(f"Error listando archivos: {e}")
            raise HTTPException(status_code=500, detail=f"Error listando archivos: {e}")

storage_service = StorageService()