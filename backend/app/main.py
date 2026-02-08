from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query, Request, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime

from .config import settings
from .core.logging import setup_logging

# 立即初始化统一日志，必须在导入其他业务模块之前，确保所有 module-level logger 正确继承配置
setup_logging()

from . import models, schemas, database, utils

# 确保所有模型已加载，并自动创建数据库表 (如果不存在)
# 这一步必须在任何数据库查询发生之前执行
models.Base.metadata.create_all(bind=database.engine)
from .repositories.ontology_repo import OntologyRepository
from .repositories.webhook_repo import WebhookRepository
from .services.ontology_service import OntologyService
from .services.webhook_service import WebhookService
from .tasks import parse_ontology_task
from .core.middleware import LoggingMiddleware
from .routers import templates

app = FastAPI(
    title=settings.APP_NAME,
    description="专业级的本体管理枢纽 - 支持版本控制、异步推送与解耦架构",
    version=settings.APP_VERSION
)

@app.on_event("startup")
async def startup_event():
    import logging
    logging.info("FastAPI application is starting up...")

# 注册路由
app.include_router(templates.router)

# 注册中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
    template_id: str = Form(None, description="解析模板 ID"),
    file: UploadFile = File(..., description="本体 ZIP 包"),
    service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    # Check if series exists
    existing_version = service.onto_repo.get_latest_version(code)
    if existing_version > 0:
         raise HTTPException(status_code=400, detail=f"Ontology code '{code}' already exists. Use POST /api/ontologies/{code}/versions to add a new version.")

    package = await service.create_ontology(file, code=code, custom_id=custom_id, name=name, template_id=template_id)
    
    # Broadcast Webhook
    _broadcast_activation(package, service, webhook_service, background_tasks)
    
    # Trigger Parsing Logic
    # If template_id provided in form, use it.
    # If not, use the one inherited/saved in package.
    final_template_id = template_id or package.template_id
    if final_template_id:
        background_tasks.add_task(parse_ontology_task, package.id, final_template_id)
        
    return package

@app.post("/api/ontologies/{code}/versions", response_model=schemas.OntologyPackageResponse, status_code=201)
async def add_ontology_version(
    code: str,
    background_tasks: BackgroundTasks,
    custom_id: str = Form(None, description="自定义版本ID (Optional)"),
    template_id: str = Form(None, description="解析模板 ID"),
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
    # Get latest package to reuse name?
    # The service.create_ontology allows name=None.
    package = await service.create_ontology(file, code=code, custom_id=custom_id, name=None, template_id=template_id)
    
    # Broadcast Webhook
    _broadcast_activation(package, service, webhook_service, background_tasks)
    
    # Trigger Parsing Logic
    final_template_id = template_id or package.template_id
    if final_template_id:
        background_tasks.add_task(parse_ontology_task, package.id, final_template_id)
        
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
        ontology_name=package.code, # Use Code for strict filtering
        background_tasks=background_tasks,
        file_path=service.get_source_zip_path(package.id)
    )

@app.post("/api/webhooks", response_model=schemas.WebhookResponse, status_code=201)
def create_webhook(
    webhook: schemas.WebhookCreate,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.create_webhook(webhook)

@app.get("/api/webhooks", response_model=schemas.PaginatedWebhookResponse)
def list_webhooks(
    skip: int = 0, 
    limit: int = 100,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_webhooks(skip, limit)

# Include Template Router
from .routers import templates
app.include_router(templates.router)

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

@app.get("/api/webhooks/{id}/logs", response_model=schemas.PaginatedWebhookDeliveryResponse)
def get_webhook_logs(
    id: str,
    ontology_name: str = Query(None, description="按本体编码/名称过滤"),
    status: str = Query(None, description="按状态过滤 (SUCCESS/FAILURE)"),
    skip: int = 0,
    limit: int = 20,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_logs_by_webhook(id, ontology_name, status, skip, limit)

@app.post("/api/webhooks/{id}/ping")
async def ping_webhook(
    id: str,
    service: WebhookService = Depends(get_webhook_service)
):
    return await service.ping_webhook(id)

@app.get("/api/ontologies", response_model=schemas.PaginatedOntologyResponse)
def get_ontologies(
    skip: int = 0, 
    limit: int = 100, 
    name: str = None,
    code: str = None,
    # all_versions is deprecated for this endpoint, it now serves Series List (active/latest)
    service: OntologyService = Depends(get_ontology_service)
):
    return service.list_ontologies(skip, limit, name, code, all_versions=False)

@app.get("/api/ontologies/{code}/versions", response_model=schemas.PaginatedOntologyResponse)
def get_ontology_versions(
    code: str,
    skip: int = 0,
    limit: int = 100,
    service: OntologyService = Depends(get_ontology_service)
):
    """获取指定本体的所有历史版本"""
    return service.list_versions(code, skip, limit)

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
        ontology_name=package.code, # Use Code for strict recording
        background_tasks=background_tasks,
        file_path=service.get_source_zip_path(package.id)
    )
        
    return {"status": "activated", "version": package.version}
    
@app.post("/api/ontologies/{id}/push")
async def push_ontology_to_webhook(
    id: str,
    webhook_id: str = Query(..., description="目标 Webhook ID"),
    background_tasks: BackgroundTasks = None, # Make it optional? No, required for injection
    service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    """
    **手动触发推送**
    将指定版本的本体推送到指定的 Webhook，不改变本体的激活状态。
    同步等待推送结果，以便前端展示。
    """
    # 1. 获取本体包信息
    package = service.onto_repo.get_package(id)
    if not package:
        raise HTTPException(status_code=404, detail="Ontology package not found")
        
    # 2. 获取源文件路径
    zip_path = service.get_source_zip_path(package.id)
    
    # 3. 触发单点推送 (同步)
    result = await webhook_service.trigger_subscription(package, webhook_id, background_tasks, zip_path, sync=True)
    
    return {
        "status": "pushed", 
        "package": package.code, 
        "version": package.version, 
        "target": webhook_id,
        "delivery_result": result
    }

@app.delete("/api/ontologies/{id}", status_code=204)
def delete_ontology_version(
    id: str,
    service: OntologyService = Depends(get_ontology_service)
):
    """
    **删除指定版本的本体**
    - 不能删除当前激活的版本
    - 不能删除被 Webhook 订阅引用的版本
    """
    service.delete_ontology(id)
    return None

@app.get("/api/ontologies/compare", response_model=schemas.OntologyComparisonResponse)
async def compare_ontologies(
    base_id: str = Query(..., description="基准版本ID"),
    target_id: str = Query(..., description="目标版本ID"),
    service: OntologyService = Depends(get_ontology_service)
):
    """比较两个本体版本之间的差异"""
    return await service.compare_packages(base_id, target_id)

@app.get("/api/ontologies/by-code/{code}/subscriptions")
def get_ontology_subscriptions(
    code: str,
    service: WebhookService = Depends(get_webhook_service)
):
    """获取订阅了指定本体的所有 Webhook 及其使用的版本"""
    # 直接使用 code 查询订阅,不需要先查询本体是否存在
    # 因为即使本体不存在,也可能有 webhook 订阅了它(提前注册)
    return service.get_subscription_status(name=None, code=code)

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
    # 必须先获取本体Code以过滤 Webhook
    package = onto_service.get_ontology_detail(id)
    return webhook_service.get_ontology_delivery_status(id, package.code) # Use Code

@app.get("/api/ontologies/{id}/files")
def read_ontology_file(
    id: str,
    path: str = Query(..., description="文件相对路径"),
    service: OntologyService = Depends(get_ontology_service)
):
    content = service.get_file_content(id, path)
    return {"content": content}

@app.get("/api/ontologies/{id}/graph", response_model=schemas.OntologyGraphResponse)
def get_ontology_graph(
    id: str,
    db: Session = Depends(get_db)
):
    """
    **获取本体图谱数据**
    """
    entities = db.query(models.OntologyEntity).filter(models.OntologyEntity.package_id == id).all()
    relations = db.query(models.OntologyRelation).filter(models.OntologyRelation.package_id == id).all()
    
    return {
        "nodes": entities,
        "links": relations
    }

@app.get("/api/ontologies/{id}/entities", response_model=List[schemas.OntologyEntityResponse])
def get_ontology_entities(
    id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    **获取本体实体列表**
    """
    return db.query(models.OntologyEntity).filter(models.OntologyEntity.package_id == id).offset(skip).limit(limit).all()

@app.get("/api/ontologies/{id}/relations", response_model=schemas.PaginatedOntologyRelationResponse)
def get_ontology_relations(
    id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: OntologyService = Depends(get_ontology_service)
):
    """
    **获取本体关系列表**
    """
    return service.list_relations(id, skip, limit)

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
