from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query, Request, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime

from . import models, schemas, database, utils
from .repositories.ontology_repo import OntologyRepository
from .repositories.webhook_repo import WebhookRepository
from .services.ontology_service import OntologyService
from .services.webhook_service import WebhookService

# 自动创建数据库表
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="OntoHub API",
    description="专业级的本体管理枢纽 - 支持版本控制、异步推送与解耦架构",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_webhook_service(db: Session = Depends(get_db)):
    webhook_repo = WebhookRepository(db)
    return WebhookService(webhook_repo)

def get_ontology_service(
    db: Session = Depends(get_db), 
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    onto_repo = OntologyRepository(db)
    webhook_repo = WebhookRepository(db)
    return OntologyService(onto_repo, webhook_repo, webhook_service)

@app.post("/api/ontologies", response_model=schemas.OntologyPackageResponse, status_code=201)
async def create_ontology_series(
    background_tasks: BackgroundTasks,
    code: str = Form(..., description="本体唯一编码 (Series ID)"),
    name: str = Form(None, description="显示名称"),
    custom_id: str = Form(None, description="自定义版本ID (Optional)"),
    file: UploadFile = File(..., description="本体 ZIP 包"),
    service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    # Check if code exists (for V1 creation, we might want to enforce uniqueness or just allow overwrite if version 0?)
    # For now, let's assume this endpoint is for "New Series" or "Idempotent Creation of V1".
    # But wait, if code exists, create_ontology will just add V(Max+1). 
    # The requirement is: 
    # 1. Create New Ontology: Input Code -> V1. If Code exists, Error?
    # 2. Add Version: Input Code (Select) -> V(Next).
    
    # Check if series exists
    existing_version = service.onto_repo.get_latest_version(code)
    if existing_version > 0:
         raise HTTPException(status_code=400, detail=f"Ontology code '{code}' already exists. Use POST /api/ontologies/{code}/versions to add a new version.")

    package = await service.create_ontology(file, code=code, custom_id=custom_id, name=name)
    
    # Broadcast Webhook
    _broadcast_activation(package, service, webhook_service, background_tasks)
        
    return package

@app.post("/api/ontologies/{code}/versions", response_model=schemas.OntologyPackageResponse, status_code=201)
async def add_ontology_version(
    code: str,
    background_tasks: BackgroundTasks,
    custom_id: str = Form(None, description="自定义版本ID (Optional)"),
    file: UploadFile = File(..., description="本体 ZIP 包"),
    service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    # Check if series exists
    existing_version = service.onto_repo.get_latest_version(code)
    if existing_version == 0:
         raise HTTPException(status_code=404, detail=f"Ontology code '{code}' not found. Use POST /api/ontologies to create it first.")
    
    # Inherit name from latest version if not provided? 
    # Service uses file.filename as fallback for name if name is None.
    # We should probably get the name from the previous version to keep it consistent?
    # Let's get the active package or latest package to copy the name.
    # For now, let service handle it (it uses filename).
    # Ideally, we should pass the existing name.
    
    # Get latest package to reuse name?
    # The service.create_ontology allows name=None.
    package = await service.create_ontology(file, code=code, custom_id=custom_id, name=None)
    
    # Broadcast Webhook
    _broadcast_activation(package, service, webhook_service, background_tasks)
        
    return package

def _broadcast_activation(package, service, webhook_service, background_tasks):
    payload = {
        "event": "ontology.activated",
        "package_id": package.id,
        "code": package.code,
        "name": package.name,
        "version": package.version,
        "is_active": True,
        "is_uploaded": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    webhook_service.broadcast_event(
        event_type="ontology.activated",
        payload=payload,
        ontology_name=package.name, # TODO: Filter by Code?
        background_tasks=background_tasks,
        file_path=service.get_source_zip_path(package.id)
    )

@app.post("/api/webhooks", response_model=schemas.WebhookResponse, status_code=201)
def create_webhook(
    webhook: schemas.WebhookCreate,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.create_webhook(webhook)

@app.get("/api/webhooks", response_model=List[schemas.WebhookResponse])
def list_webhooks(
    skip: int = 0, 
    limit: int = 100,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_webhooks(skip, limit)

@app.delete("/api/webhooks/{id}", status_code=204)
def delete_webhook(
    id: str,
    service: WebhookService = Depends(get_webhook_service)
):
    service.delete_webhook(id)
    return None

@app.put("/api/webhooks/{id}", response_model=schemas.WebhookResponse)
def update_webhook(
    id: str,
    webhook: schemas.WebhookCreate,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.update_webhook(id, webhook)

@app.get("/api/webhooks/{id}/logs", response_model=List[schemas.WebhookDeliveryResponse])
def get_webhook_logs(
    id: str,
    skip: int = 0,
    limit: int = 20,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_logs_by_webhook(id, skip, limit)

@app.post("/api/webhooks/{id}/ping")
async def ping_webhook(
    id: str,
    service: WebhookService = Depends(get_webhook_service)
):
    return await service.ping_webhook(id)

@app.get("/api/ontologies", response_model=List[schemas.OntologyPackageResponse])
def get_ontologies(
    skip: int = 0, 
    limit: int = 100, 
    name: str = None,
    code: str = None,
    all_versions: bool = False,
    service: OntologyService = Depends(get_ontology_service)
):
    return service.list_ontologies(skip, limit, name, code, all_versions)

@app.post("/api/ontologies/{id}/activate")
def activate_ontology(
    id: str,
    background_tasks: BackgroundTasks,
    service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    package = service.activate_ontology(id)
    
    payload = {
        "event": "ontology.activated",
        "package_id": package.id,
        "name": package.name,
        "version": package.version,
        "is_active": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    webhook_service.broadcast_event(
        event_type="ontology.activated",
        payload=payload,
        ontology_name=package.name,
        background_tasks=background_tasks,
        file_path=service.get_source_zip_path(package.id)
    )
        
    return {"status": "activated", "version": package.version}

@app.get("/api/ontologies/compare", response_model=schemas.OntologyComparisonResponse)
async def compare_ontologies(
    base_id: str = Query(..., description="基准版本ID"),
    target_id: str = Query(..., description="目标版本ID"),
    service: OntologyService = Depends(get_ontology_service)
):
    """比较两个本体版本之间的差异"""
    return await service.compare_packages(base_id, target_id)

@app.get("/api/ontologies/{id}", response_model=schemas.OntologyPackageDetailResponse)
def get_ontology_detail(
    id: str,
    service: OntologyService = Depends(get_ontology_service)
):
    return service.get_ontology_detail(id)

@app.get("/api/ontologies/{id}/deliveries")
def get_ontology_deliveries(
    id: str,
    onto_service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    """
    **获取本体包的 Webhook 推送状态**
    """
    # 必须先获取本体名称以过滤 Webhook
    package = onto_service.get_ontology_detail(id)
    return webhook_service.get_ontology_delivery_status(id, package.name)

@app.get("/api/ontologies/{id}/files")
def read_ontology_file(
    id: str,
    path: str = Query(..., description="文件相对路径"),
    service: OntologyService = Depends(get_ontology_service)
):
    content = service.get_file_content(id, path)
    return {"content": content}

# Static Mounting Logic
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST_DIR = os.path.join(PROJECT_ROOT, "frontend", "dist")

if os.path.exists(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api"):
             raise HTTPException(status_code=404, detail="Not Found")
        
        possible_file = os.path.join(DIST_DIR, full_path)
        if os.path.exists(possible_file) and os.path.isfile(possible_file):
            return FileResponse(possible_file)
            
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
