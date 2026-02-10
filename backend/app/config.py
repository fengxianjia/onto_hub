import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "OntoHub"
    APP_VERSION: str = "2.1.0"
    
    # Environment: development, production, test
    # Usage: APP_ENV=test pytest
    ENV: str = os.getenv("APP_ENV", "development")
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Database
    DATABASE_URL: str = ""
    
    # Storage
    STORAGE_DIR: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Avoid recursion during reload
        if not kwargs.get("_is_reloading"):
            self.setup_paths()

    def setup_paths(self):
        """Logic to setup paths based on current environment state."""
        # 0. Sync ENV again from environment
        self.ENV = os.getenv("APP_ENV", "development")
        
        # 1. Logging Directory
        if not self.LOG_DIR:
            self.LOG_DIR = os.path.join(self.BASE_DIR, "logs")
            
        # 2. Storage Directory Isolation
        if self.ENV == "test" or os.getenv("PYTEST_CURRENT_TEST"):
            self.STORAGE_DIR = os.path.join(self.BASE_DIR, "tests", "test_storage")
        elif not self.STORAGE_DIR:
            self.STORAGE_DIR = os.path.join(self.BASE_DIR, "data", "ontohub_storage")
        
        if self.STORAGE_DIR:
            os.makedirs(self.STORAGE_DIR, exist_ok=True)
                
        # 3. Database URL
        if not self.DATABASE_URL or self.DATABASE_URL.startswith("sqlite"):
            if self.ENV == "test" or os.getenv("PYTEST_CURRENT_TEST"):
                self.DATABASE_URL = "sqlite:///:memory:"
            else:
                db_path = os.path.join(self.BASE_DIR, "data", "ontohub.db")
                self.DATABASE_URL = f"sqlite:///{db_path}"

    def reload(self):
        """Force re-read environment variables and re-setup paths."""
        # Create a new instance without triggering its setup_paths immediately
        new_settings = Settings(_is_reloading=True)
        # Use model_fields from class to avoid deprecation warning
        for field in self.__class__.model_fields:
            setattr(self, field, getattr(new_settings, field))
        self.setup_paths()
        
        # CRITICAL: Reset database state so it picks up the new DATABASE_URL
        from .database import reset_db_state
        reset_db_state()

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"  # Allow internal flags like _is_reloading
    )

settings = Settings()
