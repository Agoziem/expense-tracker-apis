from pydantic import computed_field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os


# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):

    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "postgresql+asyncpg://postgres:Sirnduu1@localhost:5432/edufacilis_schools_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://default:Sirnduu1@localhost:6379/0")

    # App settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "FastAPI App")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    DOMAIN: str = os.getenv("DOMAIN", "http://localhost:8000")

    # Auth Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "secret")
    ACCESS_TOKEN_EXPIRY: int = int(os.getenv("ACCESS_TOKEN_EXPIRY", 172800))
    REFRESH_TOKEN_EXPIRY: int = int(os.getenv("REFRESH_TOKEN_EXPIRY", 604800))

    # Email Settings
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "your-resend-api-key")
    SENDER_NAME: str = os.getenv("SENDER_NAME", "Expense Tracker App")

    # AWS S3 Settings
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "your-bucket-name")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "your-access-key-id")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "your-secret-access-key")

    class Config:
        env_file = ".env"  # Load from .env file
        env_file_encoding = "utf-8"


# Create an instance of settings
settings = Settings()
