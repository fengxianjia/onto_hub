from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base

def generate_uuid():
    """生成 UUID 字符串"""
    return str(uuid.uuid4())

class OntologyPackage(Base):
    """
    本体包模型
    存储本体包的元数据
    """
    __tablename__ = "ontology_packages"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    code = Column(String, index=True, nullable=True, comment="本体唯一编码 (Series ID)")
    name = Column(String, index=True, comment="本体显示名称")
    description = Column(Text, nullable=True, comment="描述")
    upload_time = Column(DateTime, default=datetime.utcnow, comment="上传时间")
    status = Column(String, default="UPLOADING", comment="状态: UPLOADING, PROCESSING, READY, ERROR")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    
    # Versioning
    version = Column(Integer, default=1, comment="版本号")
    is_active = Column(Boolean, default=False, comment="是否启用/当前版本")

    # 关联文件
    # cascade="all, delete-orphan": 当本体包被删除时，自动删除关联的文件记录
    files = relationship("OntologyFile", back_populates="package", cascade="all, delete-orphan")

class OntologyFile(Base):
    """
    本体文件模型
    存储本体包内的文件信息
    """
    __tablename__ = "ontology_files"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    package_id = Column(String, ForeignKey("ontology_packages.id"), nullable=False, comment="所属本体包ID")
    file_path = Column(String, nullable=False, comment="文件相对路径 (e.g. concepts/user.md)")
    file_size = Column(Integer, default=0, comment="文件大小(Bytes)")
    content_preview = Column(Text, nullable=True, comment="内容预览")

    # 关联本体包
    package = relationship("OntologyPackage", back_populates="files")

class Webhook(Base):
    """
    Webhook 订阅模型
    用于远程事件通知
    """
    __tablename__ = "webhooks"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, default="Webhook", comment="订阅名称")
    target_url = Column(String, nullable=False, comment="回调地址")
    event_type = Column(String, default="ontology.activated", comment="订阅事件类型")
    # 新增过滤字段: 如果为空则订阅所有；如果有值则仅订阅名称匹配的本体
    ontology_filter = Column(String, nullable=True, comment="指定订阅的本体名称")
    # 安全加固: 签名令牌
    secret_token = Column(String, nullable=True, comment="签名令牌 (用于 HMAC 校验)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关联执行日志
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

class WebhookDelivery(Base):
    """
    Webhook 执行日志
    记录每次推送的结果
    """
    __tablename__ = "webhook_deliveries"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    webhook_id = Column(String, ForeignKey("webhooks.id"), nullable=False)
    event_type = Column(String, nullable=False)
    # 性能加固: 直接存储本体名称并建立索引，避免昂贵的 JSON 搜索
    ontology_name = Column(String, index=True, nullable=True, comment="所属本体名称")
    payload = Column(Text, nullable=True)  # maybe JSON string
    status = Column(String, nullable=False) # SUCCESS, FAILURE
    response_status = Column(Integer, nullable=True) # HTTP Code
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    webhook = relationship("Webhook", back_populates="deliveries")
