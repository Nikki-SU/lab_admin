from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    HUB_HOST: str = "0.0.0.0"
    HUB_PORT: int = 8000
    HUB_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "sqlite:///./labvault.db"
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    STORAGE_PATH: str = "./storage"
    DATA_ZONE_PATH: str = "./storage/data"
    COLLAB_ZONE_PATH: str = "./storage/collab"
    PERMISSION_EXPIRY_WARNING_DAYS: str = "30,7,1"
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
