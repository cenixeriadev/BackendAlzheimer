import os
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
import base64
from typing import Dict, Optional
from app.config import settings

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=boto3.session.Config(signature_version='s3v4'),
            verify=False  # Solo HTTP
        )
        
        self.bucket_name = settings.AWS_BUCKET_NAME
        self.setup_bucket()
    
    def setup_bucket(self):
        """Crear el bucket si no existe"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f" Bucket '{self.bucket_name}' ya existe")
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                print(f" Bucket '{self.bucket_name}' creado exitosamente")
                
                self._setup_bucket_policy()
                
            except ClientError as e:
                print(f" Error creando bucket: {e}")
                raise HTTPException(status_code=500, detail=f"Error configurando storage: {e}")
    
    def _setup_bucket_policy(self):
        """Configurar política del bucket para permitir acceso público de lectura"""
        try:
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                    }
                ]
            }
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=str(policy).replace("'", '"')
            )
            print("✅ Política de bucket configurada")
        except Exception as e:
            print(f"⚠️  No se pudo configurar la política del bucket: {e}")

    async def upload_file(self, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> Dict[str, str]:
        """Subir archivo al storage"""
        try:
            # Generar nombre único para el archivo
            file_extension = filename.split('.')[-1] if '.' in filename else 'bin'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Subir archivo
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_content,
                ContentType=content_type,
                ACL='public-read' 
            )
            
            # Generar URL del archivo
            file_url = f"{settings.AWS_ENDPOINT_URL}/{self.bucket_name}/{unique_filename}"
            
            return {
                "filename": unique_filename,
                "url": file_url,
                "message": "Archivo subido exitosamente"
            }
            
        except ClientError as e:
            print(f" Error subiendo archivo: {e}")
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
            print(f" Error procesando imagen base64: {e}")
            raise HTTPException(status_code=500, detail=f"Error procesando imagen: {e}")

    def _get_content_type_from_base64(self, base64_string: str) -> str:
        """Determinar el tipo de contenido desde el string base64"""
        if base64_string.startswith('/9j/') or base64_string.startswith('iVBOR'):
            return "image/jpeg"
        elif base64_string.startswith('iVBORw'):
            return "image/png"
        elif base64_string.startswith('R0lGOD'):
            return "image/gif"
        else:
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
            print(f" Error eliminando archivo: {e}")
            raise HTTPException(status_code=500, detail=f"Error eliminando archivo: {e}")

    async def get_file_url(self, filename: str) -> str:
        """Obtener URL del archivo"""
        return f"{settings.AWS_ENDPOINT_URL}/{self.bucket_name}/{filename}"

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
                        'url': f"{settings.AWS_ENDPOINT_URL}/{self.bucket_name}/{obj['Key']}"
                    })
            
            return files
            
        except ClientError as e:
            print(f" Error listando archivos: {e}")
            raise HTTPException(status_code=500, detail=f"Error listando archivos: {e}")

storage_service = StorageService()