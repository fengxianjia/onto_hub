from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class OntologyFileBase(BaseModel):
    file_path: str
    file_size: int
    content_preview: Optional[str] = None

class OntologyFileResponse(OntologyFileBase):
    id: str
    package_id: str

    model_config = ConfigDict(from_attributes=True)

class OntologyPackageBase(BaseModel):
    name: str
    code: Optional[str] = None
    version: int = 1
    is_active: bool = False

class OntologyPackageCreate(OntologyPackageBase):
    description: Optional[str] = None
    template_id: Optional[str] = None

class OntologyPackageResponse(OntologyPackageBase):
    id: str
    description: Optional[str] = None
    upload_time: datetime
    status: str
    error_msg: Optional[str] = None
    file_count: int = 0
    is_updated: bool = False
    
    # Deletion safety flags
    is_deletable: bool = True
    deletable_reason: Optional[str] = None

    template_id: Optional[str] = None
    template_name: Optional[str] = None
    subscriber_count: Optional[int] = 0
    
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
    name: Optional[str] = "Webhook"
    target_url: str
    event_type: str = "ontology.activated"
    ontology_filter: Optional[str] = None
    secret_token: Optional[str] = None # 用于加固

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
    name: str
    description: Optional[str] = None
    rules: str # JSON string

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

# --- Auth & User Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
