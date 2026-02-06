from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 数据库 URL
# 数据库文件将存储在当前目录下的 ontohub.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./ontohub.db"

# 创建数据库引擎
# connect_args={"check_same_thread": False} 是 SQLite 特有的配置，
# 允许在多线程中共享连接（FastAPI 通常在大并发下使用线程池）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建会话工厂
# autocommit=False: 禁止自动提交，需要手动 commit，保证事务控制
# autoflush=False: 禁止自动刷新，需要手动 flush
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类，所有模型都继承自这个类
Base = declarative_base()

# 获取数据库会话的依赖函数 (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
