from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query, Request, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List
import os
from datetime import datetime, UTC

from .config import settings
from .core.logging import setup_logging

# 立即初始化统一日志
setup_logging()

from .core.errors import BusinessException, BusinessCode, handle_result
from fastapi.responses import JSONResponse

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging
    logging.info("FastAPI application is starting up...")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="专业级的本体管理枢纽 - 支持版本控制、异步推送与解耦架构",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

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

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.business_code,
            "detail": exc.detail or "Business error occurred"
        }
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
    auto_push: bool = Form(True, description="是否立即推送给订阅者"),
    file: UploadFile = File(..., description="本体 ZIP 包"),
    service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    result = await service.create_ontology(file, code=code, custom_id=custom_id, name=name, template_id=template_id, is_initial=True)
    package = handle_result(result)
    
    # Check for subscribers
    matching_webhooks = webhook_service.repo.get_webhooks_by_event("ontology.activated", ontology_name=code)
    subscriber_count = len(matching_webhooks)

    # Broadcast Webhook only if auto_push is True
    if auto_push:
        _broadcast_activation(package, service, webhook_service, background_tasks)
    
    # Set subscriber count for response
    package_resp = schemas.OntologyPackageResponse.model_validate(package)
    package_resp.subscriber_count = subscriber_count

    # Trigger Parsing Logic
    final_template_id = template_id or package.template_id
    if final_template_id:
        background_tasks.add_task(parse_ontology_task, package.id, final_template_id)
        
    return package_resp

@app.post("/api/ontologies/{code}/versions", response_model=schemas.OntologyPackageResponse, status_code=201)
async def add_ontology_version(
    code: str,
    background_tasks: BackgroundTasks,
    custom_id: str = Form(None, description="自定义版本ID (Optional)"),
    template_id: str = Form(None, description="解析模板 ID"),
    auto_push: bool = Form(True, description="是否立即推送给订阅者"),
    file: UploadFile = File(..., description="本体 ZIP 包"),
    service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    result = await service.create_ontology(file, code=code, custom_id=custom_id, name=None, template_id=template_id, is_initial=False)
    package = handle_result(result)
    
    # Check for subscribers
    matching_webhooks = webhook_service.repo.get_webhooks_by_event("ontology.activated", ontology_name=code)
    subscriber_count = len(matching_webhooks)

    # Broadcast Webhook only if auto_push is True
    if auto_push:
        _broadcast_activation(package, service, webhook_service, background_tasks)
    
    # Set subscriber count for response
    package_resp = schemas.OntologyPackageResponse.model_validate(package)
    package_resp.subscriber_count = subscriber_count

    # Trigger Parsing Logic
    final_template_id = template_id or package.template_id
    if final_template_id:
        background_tasks.add_task(parse_ontology_task, package.id, final_template_id)
        
    return package_resp

@app.patch("/api/ontologies/{code}", response_model=schemas.OntologyPackageResponse)
async def update_ontology_metadata(
    code: str,
    series_in: schemas.OntologySeriesUpdate,
    service: OntologyService = Depends(get_ontology_service)
):
    """更新本体元数据 (名称、描述、默认模板)"""
    result = await service.update_ontology_series(code, series_in)
    series = handle_result(result)
    
    # Return latest version info as a convenience
    latest_version = service.onto_repo.get_latest_version(code)
    package = service.onto_repo.get_active_package_by_code(code)
    if not package:
        # Get latest
        pkg_list, _ = service.onto_repo.list_packages(latest_version, limit=1)
        package = pkg_list[0] if pkg_list else None
    
    if not package:
         raise HTTPException(status_code=404, detail="No versions found for this ontology")
         
    return package

@app.post("/api/ontologies/packages/{package_id}/reparse")
async def reparse_ontology(
    package_id: str,
    background_tasks: BackgroundTasks,
    req: schemas.OntologyReparseRequest = None,
    service: OntologyService = Depends(get_ontology_service)
):
    """重新触发本体解析"""
    template_id = req.template_id if req else None
    result = await service.reparse_ontology_package(package_id, template_id)
    final_template_id = handle_result(result)
    
    background_tasks.add_task(parse_ontology_task, package_id, final_template_id)
    return {"message": "Parsing task triggered", "template_id": final_template_id}

def _broadcast_activation(package, service, webhook_service, background_tasks):
    payload = {
        "event": "ontology.activated",
        "package_id": package.id,
        "code": package.code,
        "name": package.name,
        "version": package.version,
        "is_active": True,
        "is_uploaded": True,
        "timestamp": datetime.now(UTC).isoformat()
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
    result = service.create_webhook(webhook)
    return handle_result(result)

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
    result = service.update_webhook(id, webhook)
    return handle_result(result)

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
    result = await service.ping_webhook(id)
    return handle_result(result)

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
    result = service.activate_ontology(id)
    package = handle_result(result)
    
    payload = {
        "event": "ontology.activated",
        "package_id": package.id,
        "name": package.name,
        "version": package.version,
        "is_active": True,
        "timestamp": datetime.now(UTC).isoformat()
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
    # 1. 获取本体详情 (包含了 path 获取逻辑，虽然 trigger_subscription 本身需要 package 对象，我们先获取结果)
    pkg_result = service.get_ontology_detail(id)
    package_detail = handle_result(pkg_result)
    
    # 获取 DB 对象用于推送
    package = service.onto_repo.get_package(id)
    
    # 2. 获取源文件路径
    zip_path = service.get_source_zip_path(package.id)
    
    # 3. 触发单点推送 (同步)
    push_result = await webhook_service.trigger_subscription(package, webhook_id, background_tasks, zip_path, sync=True)
    result_data = handle_result(push_result)
    
    return {
        "status": "pushed", 
        "package": package.code, 
        "version": package.version, 
        "target": webhook_id,
        "delivery_result": result_data
    }

@app.delete("/api/ontologies/{id}", status_code=204)
def delete_ontology_version(
    id: str,
    service: OntologyService = Depends(get_ontology_service)
):
    """
    **删除指定版本的本体**
    - 不能删除当前激活的版本
    """
    result = service.delete_version(id)
    handle_result(result)
    return None

@app.delete("/api/ontologies/by-code/{code}", status_code=204)
def delete_ontology_series(
    code: str,
    service: OntologyService = Depends(get_ontology_service)
):
    """
    **删除整个本体系列 (高危)**
    """
    result = service.delete_ontology_series(code)
    handle_result(result)
    return None

@app.get("/api/ontologies/compare", response_model=schemas.OntologyComparisonResponse)
async def compare_ontologies(
    base_id: str = Query(..., description="基准版本ID"),
    target_id: str = Query(..., description="目标版本ID"),
    service: OntologyService = Depends(get_ontology_service)
):
    """比较两个本体版本之间的差异"""
    result = await service.compare_packages(base_id, target_id)
    return handle_result(result)

@app.get("/api/ontologies/by-code/{code}/subscriptions")
def get_ontology_subscriptions(
    code: str,
    service: WebhookService = Depends(get_webhook_service)
):
    """获取订阅了指定本体的所有 Webhook 及其使用的版本"""
    return service.get_subscription_status(name=None, code=code)

@app.get("/api/ontologies/{id}", response_model=schemas.OntologyPackageDetailResponse)
def get_ontology_detail(
    id: str,
    service: OntologyService = Depends(get_ontology_service)
):
    result = service.get_ontology_detail(id)
    return handle_result(result)

@app.get("/api/ontologies/{id}/deliveries")
def get_ontology_deliveries(
    id: str,
    onto_service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    """
    **获取本体包的 Webhook 推送状态**
    """
    pkg_result = onto_service.get_ontology_detail(id)
    package = handle_result(pkg_result)
    return webhook_service.get_ontology_delivery_status(id, package.code)

@app.get("/api/ontologies/{id}/files")
def read_ontology_file(
    id: str,
    path: str = Query(..., description="文件相对路径"),
    service: OntologyService = Depends(get_ontology_service)
):
    result = service.get_file_content(id, path)
    return {"content": handle_result(result)}

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
