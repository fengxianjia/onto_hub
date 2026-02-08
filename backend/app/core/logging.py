import os
import logging
import logging.config
from typing import Dict, Any

from .config import settings

# 日志存储目录
LOG_DIR = settings.LOG_DIR

def setup_logging(level: str = settings.LOG_LEVEL):
    """
    统一日志配置初始化
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    log_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d (%(funcName)s): %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": "detailed",
                "filename": os.path.join(LOG_DIR, "ontohub.log"),
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console", "file"],
                "level": level,
                "propagate": True,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING", # 仅记录警告及以上，避免过多的 SQL 打印
                "handlers": ["console", "file"],
                "propagate": False,
            }
        },
    }

    logging.config.dictConfig(log_config)
    logging.info(f"Logging initialized. Log level: {level}, Directory: {LOG_DIR}")
