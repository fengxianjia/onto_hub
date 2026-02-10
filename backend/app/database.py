from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# Global state for database components
_engine = None
_SessionLocal = None

def reset_db_state():
    """Reset global database state. Useful for testing when settings change."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None

from sqlalchemy.pool import StaticPool

def get_engine():
    global _engine
    if _engine is None:
        kwargs = {}
        if "sqlite" in settings.DATABASE_URL:
            kwargs["connect_args"] = {"check_same_thread": False}
            # For in-memory databases, we MUST use a StaticPool to share connection
            if ":memory:" in settings.DATABASE_URL:
                kwargs["poolclass"] = StaticPool
        
        _engine = create_engine(settings.DATABASE_URL, **kwargs)
    return _engine

# Export engine as a proxy that behaves like the engine
class EngineProxy:
    def __getattr__(self, name):
        return getattr(get_engine(), name)
    def __setattr__(self, name, value):
        setattr(get_engine(), name, value)
    def __repr__(self):
        return repr(get_engine())

engine = EngineProxy()

def SessionLocal(*args, **kwargs):
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal(*args, **kwargs)

# 声明基类
Base = declarative_base()

# 获取数据库会话的依赖函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
