import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "OntoHub"
    APP_VERSION: str = "2.1.0"
    
    # Environment
    ENV: str = "development"
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Database
    DATABASE_URL: str = "sqlite:///./ontohub.db"
    
    # Storage
    # Default to 'backend/data/ontohub_storage' relative to BASE_DIR if not provided
    STORAGE_DIR: str = os.path.join(
        os.path.dirname(BASE_DIR), # backend/
        "data", 
        "ontohub_storage"
    )

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = os.path.join(
        os.path.dirname(BASE_DIR), # backend/
        "logs"
    )

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
