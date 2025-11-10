from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    AWS_ENDPOINT_URL: Optional[str] = None
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "alzheimer-images")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if os.getenv("ENVIROMENT") != "production" and self.AWS_ENDPOINT_URL is None:
            self.AWS_ENDPOINT_URL = "http://localhost:9000"

    class Config:
        env_file = ".env"


settings = Settings()