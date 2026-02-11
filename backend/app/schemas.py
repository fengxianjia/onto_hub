from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any
from datetime import datetime

class OntologyFileBase(BaseModel):
    file_path: str = Field(..., description="文件在包内的相对路径", examples=["src/core.owl"])
    file_size: int = Field(..., description="文件大小 (Bytes)", examples=[10240])
    content_preview: Optional[str] = Field(None, description="内容预览 (部分截断)")

class OntologyFileResponse(OntologyFileBase):
    id: str = Field(..., description="文件记录 UUID")
    package_id: str = Field(..., description="所属本体包 UUID")

    model_config = ConfigDict(from_attributes=True)

class OntologyPackageBase(BaseModel):
    name: str = Field(..., description="显示名称", examples=["企业核心本体"])
    code: Optional[str] = Field(None, description="本体唯一编码 (Slug)", examples=["eco"])
    version: int = Field(1, description="版本序列号", examples=[1])
    is_active: bool = Field(False, description="是否为当前生效的主版本")

class OntologyPackageCreate(OntologyPackageBase):
    description: Optional[str] = Field(None, description="版本更新说明")
    template_id: Optional[str] = Field(None, description="指定的解析模板 ID")

class OntologyPackageResponse(OntologyPackageBase):
    id: str = Field(..., description="本体包 UUID")
    description: Optional[str] = Field(None, description="本体详细描述")
    upload_time: datetime = Field(..., description="上传时间")
    status: str = Field(..., description="处理状态 (READY/PARSING/ERROR)", examples=["READY"])
    error_msg: Optional[str] = Field(None, description="解析失败时的错误详细信息")
    file_count: int = Field(0, description="包内文件总数")
    is_updated: bool = Field(False, description="相比上一版本是否有内容实质变更")
    
    # Deletion safety flags
    is_deletable: bool = Field(True, description="是否允许物理删除")
    deletable_reason: Optional[str] = Field(None, description="不可删除时的原因说明")

    template_id: Optional[str] = Field(None, description="绑定的解析模板 ID")
    template_name: Optional[str] = Field(None, description="模板名称")
    subscriber_count: Optional[int] = Field(0, description="当前的订阅订阅者数量")
    
    model_config = ConfigDict(from_attributes=True)

class OntologySeriesUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_template_id: Optional[str] = None

class OntologyReparseRequest(BaseModel):
    template_id: Optional[str] = None

class OntologyPackageDetailResponse(OntologyPackageResponse):
    files: List[OntologyFileResponse] = []

class PaginatedOntologyResponse(BaseModel):
    items: List[OntologyPackageResponse]
    total: int

class WebhookBase(BaseModel):
    name: Optional[str] = Field("Webhook", description="回调配置名称", examples=["钉钉通知"])
    target_url: str = Field(..., description="接收 POST 请求的目标 URL", examples=["https://api.example.com/webhook"])
    event_type: str = Field("ontology.activated", description="触发事件类型 (ontology.activated)", examples=["ontology.activated"])
    ontology_filter: Optional[str] = Field(None, description="过滤特定的本体编码，为空则订阅所有", examples=["eco"])
    secret_token: Optional[str] = Field(None, description="用于签名验证的共享密钥 (签名算法: HMAC-SHA256)")

class WebhookCreate(WebhookBase):
    pass

class WebhookResponse(WebhookBase):
    id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PaginatedWebhookResponse(BaseModel):
    items: List[WebhookResponse]
    total: int

class WebhookDeliveryResponse(BaseModel):
    id: str
    webhook_id: str
    webhook_name: Optional[str] = None # 用于 UI 显示
    event_type: str
    ontology_name: Optional[str] = None # 用于性能优化
    payload: str | None = None  # Add this field
    status: str
    response_status: int | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedWebhookDeliveryResponse(BaseModel):
    items: List[WebhookDeliveryResponse]
    total: int

class FileDiff(BaseModel):
    file_path: str
    status: str # "added", "deleted", "modified", "unchanged"
    base_content: Optional[str] = None
    target_content: Optional[str] = None

class OntologyComparisonResponse(BaseModel):
    base_version: int
    target_version: int
    files: List[FileDiff]

class ParsingTemplateBase(BaseModel):
    name: str = Field(..., description="模板名称", examples=["标准 Markdown 语义模板"])
    description: Optional[str] = Field(None, description="模板详细描述")
    parser_type: str = Field("markdown", description="解析器核心类型 (markdown/owl/custom)", examples=["markdown"])
    rules: str = Field(..., description="JSON 序列化的解析规则字符串", examples=[
        '{"entity": {"name_source": "filename_no_ext"}, "relation": {"strategies": ["wikilink"]}}'
    ])

class ParsingTemplateCreate(ParsingTemplateBase):
    pass

class ParsingTemplateResponse(ParsingTemplateBase):
    id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class OntologyEntityResponse(BaseModel):
    id: str
    package_id: str
    name: str
    category: Optional[str] = None
    metadata_json: Optional[str] = None
    file_path: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class OntologyRelationResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    
    model_config = ConfigDict(from_attributes=True)

class OntologyGraphResponse(BaseModel):
    nodes: List[OntologyEntityResponse]
    links: List[OntologyRelationResponse]

class OntologyRelationDetailResponse(OntologyRelationResponse):
    source: OntologyEntityResponse
    target: OntologyEntityResponse

class PaginatedOntologyRelationResponse(BaseModel):
    items: List[OntologyRelationDetailResponse]
    total: int

