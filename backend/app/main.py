from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query, Request, BackgroundTasks
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
async def upload_ontology(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="本体 ZIP 包"),
    service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    package = await service.create_ontology(file)
    
    # Broadcast Webhook
    payload = {
        "event": "ontology.activated",
        "package_id": package.id,
        "name": package.name,
        "version": package.version,
        "is_active": True,
        "is_uploaded": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Files are extracted in OntologyService, we point to the directory for the ZIP broadcast?
    # Original logic sent the source ZIP if possible.
    # We'll maintain the path logic.
    webhook_service.broadcast_event(
        event_type="ontology.activated",
        payload=payload,
        ontology_name=package.name,
        background_tasks=background_tasks,
        file_path=service.get_source_zip_path(package.id)
    )
        
    return package

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
    all_versions: bool = False,
    service: OntologyService = Depends(get_ontology_service)
):
    return service.list_ontologies(skip, limit, name, all_versions)

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

@app.get("/api/ontologies/{id}", response_model=schemas.OntologyPackageDetailResponse)
def get_ontology_detail(
    id: str,
    service: OntologyService = Depends(get_ontology_service)
):
    return service.get_ontology_detail(id)

@app.delete("/api/ontologies/{id}", status_code=204)
def delete_ontology(
    id: str,
    service: OntologyService = Depends(get_ontology_service)
):
    service.delete_ontology(id)
    return None

@app.get("/api/logs/ontologies")
def get_ontology_logs(
    name: str = Query(..., description="本体名称"),
    skip: int = 0,
    limit: int = 50,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_logs_by_ontology(name, skip, limit)

@app.get("/api/subscriptions/ontologies/status")
def get_subscription_status(
    name: str = Query(..., description="本体名称"),
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_subscription_status(name)

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
