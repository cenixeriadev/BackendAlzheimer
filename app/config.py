from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    AWS_ENDPOINT_URL: str ="http://localhost:9000"
    AWS_ACCESS_KEY_ID: str ="minioadmin"
    AWS_SECRET_ACCESS_KEY: str ="minioadmin"
    AWS_BUCKET_NAME: str ="alzheimer-images"

    class Config:
        env_file = ".env"


settings = Settings()
