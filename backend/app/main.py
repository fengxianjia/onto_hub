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

from .core.errors import BusinessException, BusinessCode, handle_result
from fastapi.responses import JSONResponse

from . import models, schemas, database, utils

# 数据库初始化函数
def init_db():
    models.Base.metadata.create_all(bind=database.engine)

# 在非测试环境下自动初始化
if settings.ENV != "test":
    init_db()
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
    # Initialize logging during application startup
    setup_logging()
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
    # Use the SessionLocal factory which now includes a test-environment guard
    # The dependency_overrides in conftest.py should prevent this from being executed during tests
    import os
    if os.getenv("PYTEST_CURRENT_TEST"):
        # This branch SHOULD NOT reach SessionLocal() if overrides are working
        # If it does, it's a critical failure in the test setup
        pass
        
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

@app.post(
    "/api/ontologies", 
    response_model=schemas.OntologyPackageResponse, 
    status_code=201,
    summary="创建/上传本体新版本",
    description="上传一个 ZIP 压缩包来创建本体的新版本。系统会自动触发异步解析流程。",
    tags=["Ontologies"]
)
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
        background_tasks.add_task(parse_ontology_task, package.id, final_template_id, db=service.onto_repo.db)
        
    return package_resp

@app.post(
    "/api/ontologies/{code}/versions", 
    response_model=schemas.OntologyPackageResponse, 
    status_code=201,
    summary="添加本体新版本",
    description="在现有的本体系列下上传一个新的版本文件。支持自定义版本号。",
    tags=["Ontologies"]
)
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
        background_tasks.add_task(parse_ontology_task, package.id, final_template_id, db=service.onto_repo.db)
        
    return package_resp

@app.patch(
    "/api/ontologies/{code}", 
    response_model=schemas.OntologyPackageResponse,
    summary="更新本体元数据",
    description="修改本体系列的名称、描述或默认模板信息。返回该系列当前激活或最新的版本信息。",
    tags=["Ontologies"]
)
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

@app.post(
    "/api/ontologies/packages/{package_id}/reparse", 
    response_model=schemas.OntologyPackageResponse,
    summary="重新解析本体 (异步)",
    description="使用新的模板或解析规则再次处理现有的 ZIP 包。会清除旧的解析结果并重新入库。",
    tags=["Ontologies"]
)
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
    
    background_tasks.add_task(parse_ontology_task, package_id, final_template_id, db=service.onto_repo.db)
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
        file_path=service.get_source_zip_path(package.id),
        db=service.onto_repo.db
    )

@app.post(
    "/api/webhooks", 
    response_model=schemas.WebhookResponse, 
    status_code=201,
    summary="注册新 Webhook",
    description="创建一个外部通知回调。建议配置 secret_token 以启用 HMAC-SHA256 签名校验。",
    tags=["Webhooks"]
)
async def create_webhook(
    webhook: schemas.WebhookCreate,
    service: WebhookService = Depends(get_webhook_service)
):
    result = service.create_webhook(webhook)
    return handle_result(result)

@app.get(
    "/api/webhooks", 
    response_model=schemas.PaginatedWebhookResponse,
    summary="获取 Webhook 列表",
    description="查看所有配置的外部通知回调点。",
    tags=["Webhooks"]
)
def list_webhooks(
    skip: int = 0, 
    limit: int = 100,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_webhooks(skip, limit)

# Include Template Router
from .routers import templates
app.include_router(templates.router)

@app.delete(
    "/api/webhooks/{id}", 
    status_code=204,
    summary="删除 Webhook",
    description="注销指定的 Webhook 订阅，停止向其发送通知。",
    tags=["Webhooks"]
)
def delete_webhook(
    id: str,
    service: WebhookService = Depends(get_webhook_service)
):
    service.delete_webhook(id)
    return None

@app.put(
    "/api/webhooks/{id}", 
    response_model=schemas.WebhookResponse,
    summary="更新 Webhook 配置",
    description="修改 Webhook 的目标地址、事件类型、过滤条件或安全令牌。",
    tags=["Webhooks"]
)
def update_webhook(
    id: str,
    webhook: schemas.WebhookCreate,
    service: WebhookService = Depends(get_webhook_service)
):
    result = service.update_webhook(id, webhook)
    return handle_result(result)

@app.get(
    "/api/webhooks/{id}/logs", 
    response_model=schemas.PaginatedWebhookDeliveryResponse,
    summary="获取 Webhook 交付日志",
    description="获取指定 Webhook 的历史推送记录，支持按本体名称或交付状态过滤。",
    tags=["Webhooks"]
)
def get_webhook_logs(
    id: str,
    ontology_name: str = Query(None, description="按本体编码/名称过滤"),
    status: str = Query(None, description="按状态过滤 (SUCCESS/FAILURE)"),
    skip: int = 0,
    limit: int = 20,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_logs_by_webhook(id, ontology_name, status, skip, limit)

@app.post(
    "/api/webhooks/{id}/ping",
    summary="连通性测试 (Ping)",
    description="向指定的 Webhook 目标 URL 发送一个 Ping 测试包，验证其是否可达及响应状态。",
    tags=["Webhooks"]
)
async def ping_webhook(
    id: str,
    service: WebhookService = Depends(get_webhook_service)
):
    result = await service.ping_webhook(id)
    return handle_result(result)

@app.get(
    "/api/ontologies", 
    response_model=schemas.PaginatedOntologyResponse,
    summary="获取本体系列列表",
    description="分页获取所有已注册的本体系列（不包含具体的历史版本细节）。",
    tags=["Ontologies"]
)
def get_ontologies(
    skip: int = 0, 
    limit: int = 100, 
    name: str = None,
    code: str = None,
    # all_versions is deprecated for this endpoint, it now serves Series List (active/latest)
    service: OntologyService = Depends(get_ontology_service)
):
    return service.list_ontologies(skip, limit, name, code, all_versions=False)

@app.get(
    "/api/ontologies/{code}/versions", 
    response_model=schemas.PaginatedOntologyResponse,
    summary="列出本体所有版本历史",
    description="获取特定本体系列下的所有版本记录，按上传时间倒序排列。",
    tags=["Ontologies"]
)
def get_ontology_versions(
    code: str,
    skip: int = 0,
    limit: int = 100,
    service: OntologyService = Depends(get_ontology_service)
):
    """获取指定本体的所有历史版本"""
    return service.list_versions(code, skip, limit)

@app.get(
    "/api/ontologies/{code}/versions/{version}/download",
    summary="下载指定版本的原始 ZIP 包",
    description="获取本体物理存储的原始 ZIP 上传包。支持断点续传与流式下载。",
    tags=["Ontologies"]
)
async def download_ontology_version(
    code: str,
    version: int,
    service: OntologyService = Depends(get_ontology_service)
):
    """
    **下载指定版本的原始本体 ZIP 包**
    """
    result = service.get_version_package_path(code, version)
    file_path = handle_result(result)
    
    filename = f"{code}_v{version}.zip"
    return FileResponse(
        path=file_path, 
        filename=filename,
        media_type="application/zip"
    )

@app.post(
    "/api/ontologies/{id}/activate",
    summary="激活本体特定版本",
    description="将指定的本体包标记为已激活状态，并触发 Webhook 广播推送。",
    tags=["Ontologies"]
)
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
    
@app.post(
    "/api/ontologies/{id}/push",
    summary="手动触发 Webhook 推送",
    description="将指定的本体包手动推送至特定的 Webhook 节点，不影响当前激活状态。",
    tags=["Webhooks"]
)
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

@app.delete(
    "/api/ontologies/{id}", 
    status_code=204,
    summary="删除单个本体版本",
    description="删除特定的历史版本记录。如果该版本是当前激活版本，系统可能会拒绝操作或要求先激活其他版本。",
    tags=["Ontologies"]
)
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

@app.delete(
    "/api/ontologies/by-code/{code}", 
    status_code=204,
    summary="删除整个本体系列",
    description="危险操作：级联删除该系列下的所有版本记录、解析出的实体关系以及物理存储的文件。",
    tags=["Ontologies"]
)
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

@app.get(
    "/api/ontologies/compare", 
    response_model=schemas.OntologyComparisonResponse,
    summary="差异化对比两个本体版本",
    description="对两个指定的本体包进行物理文件级别的对比，返回新增、删除和修改的文件列表及内容 Diff。",
    tags=["Ontologies"]
)
async def compare_ontologies(
    base_id: str = Query(..., description="基准版本ID"),
    target_id: str = Query(..., description="目标版本ID"),
    service: OntologyService = Depends(get_ontology_service)
):
    """比较两个本体版本之间的差异"""
    result = await service.compare_packages(base_id, target_id)
    return handle_result(result)

@app.get(
    "/api/ontologies/by-code/{code}/subscriptions",
    summary="获取本体订阅详情",
    description="查询有哪些 Webhook 订阅了该本体系列，并返回它们当前通过回调获取到的版本信息。",
    tags=["Webhooks"]
)
def get_ontology_subscriptions(
    code: str,
    service: WebhookService = Depends(get_webhook_service)
):
    """获取订阅了指定本体的所有 Webhook 及其使用的版本"""
    return service.get_subscription_status(name=None, code=code)

@app.get(
    "/api/ontologies/{id}", 
    response_model=schemas.OntologyPackageDetailResponse,
    summary="获取本体包详细信息",
    description="通过 ID 获取本体包的详细元数据，包括包内文件列表、状态及关联模板。",
    tags=["Ontologies"]
)
def get_ontology_detail(
    id: str,
    service: OntologyService = Depends(get_ontology_service)
):
    result = service.get_ontology_detail(id)
    return handle_result(result)

@app.get(
    "/api/ontologies/{id}/deliveries",
    summary="查询本体交付历史",
    description="获取指定本体包发送给各个 Webhook 的详细交付记录及结果。",
    tags=["Webhooks"]
)
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

@app.get(
    "/api/ontologies/{id}/files",
    summary="读取包内特定文件内容",
    description="通过本体 ID 和文件路径，实时读取 ZIP 包内某个文件的原文字符串。常用于预览 OWL 或 Markdown 内容。",
    tags=["Ontologies"]
)
def read_ontology_file(
    id: str,
    path: str = Query(..., description="文件相对路径"),
    service: OntologyService = Depends(get_ontology_service)
):
    result = service.get_file_content(id, path)
    return {"content": handle_result(result)}

@app.get(
    "/api/ontologies/{id}/graph", 
    response_model=schemas.OntologyGraphResponse,
    summary="获取本体关联图谱",
    description="返回该本体包解析出的所有实体(Nodes)和关系(Links)，用于前端 3D/2D 图谱展示。",
    tags=["Ontologies"]
)
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

@app.get(
    "/api/ontologies/{id}/entities", 
    response_model=List[schemas.OntologyEntityResponse],
    summary="分页获取本体实体列表",
    description="查询特定本体包解析出的所有实体对象（类、实例等），支持分页。",
    tags=["Ontologies"]
)
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

@app.get(
    "/api/ontologies/{id}/relations", 
    response_model=schemas.PaginatedOntologyRelationResponse,
    summary="分页获取本体关系列表",
    description="查询特定本体包解析出的所有语义关系（继承、属性关联等），包含源实体与目标实体的简要信息。",
    tags=["Ontologies"]
)
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
    
    @app.get(
        "/{full_path:path}",
        summary="静态资源服务 (前端入口)",
        description="负责交付 Vue 编译后的静态资源文件，并为单页应用（SPA）提供路由保底机制。",
        tags=["System"]
    )
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
