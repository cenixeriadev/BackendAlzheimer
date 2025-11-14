from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")

    AWS_ENDPOINT_URL: str = os.getenv("AWS_ENDPOINT_URL", "")  # Vacío para AWS 
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "alzheimer-images")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    @property
    def is_local_storage(self):
        return bool(self.AWS_ENDPOINT_URL and "localhost" in self.AWS_ENDPOINT_URL)

    class Config:
        env_file = ".env"

settings = Settings()