import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "OntoHub"
    APP_VERSION: str = "2.1.0"
    
    # Environment
    ENV: str = "development"
    
    # Paths
    # config.py is at backend/app/config.py
    # BASE_DIR should be backend/
    _current_file = os.path.abspath(__file__)
    BASE_DIR: str = os.path.dirname(os.path.dirname(_current_file))
    
    # Database
    # Standardize to data/ directory for volume persistence
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'ontohub.db')}"
    
    # Storage
    # Default to 'backend/data/ontohub_storage' inside BASE_DIR
    STORAGE_DIR: str = os.path.join(BASE_DIR, "data", "ontohub_storage")

    # Logging
    # Default to 'backend/logs' inside BASE_DIR
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()
