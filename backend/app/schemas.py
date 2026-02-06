from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OntologyFileBase(BaseModel):
    file_path: str
    file_size: int
    content_preview: Optional[str] = None

class OntologyFileResponse(OntologyFileBase):
    id: str
    package_id: str

    class Config:
        from_attributes = True

class OntologyPackageBase(BaseModel):
    name: str
    version: int = 1
    is_active: bool = False

class OntologyPackageCreate(OntologyPackageBase):
    description: Optional[str] = None

class OntologyPackageResponse(OntologyPackageBase):
    id: str
    description: Optional[str] = None
    upload_time: datetime
    status: str
    error_msg: Optional[str] = None
    file_count: int = 0
    is_updated: bool = False
    # New field to show successful deliveries for this version
    delivered_webhooks: Optional[List[str]] = []
    
    # Deletion safety flags
    is_deletable: bool = True
    deletable_reason: Optional[str] = None

    class Config:
        from_attributes = True

class OntologyPackageDetailResponse(OntologyPackageResponse):
    files: List[OntologyFileResponse] = []

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
    
    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True
