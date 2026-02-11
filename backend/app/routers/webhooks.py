from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, UTC

from .. import schemas, models
from ..services.webhook_service import WebhookService
from ..services.ontology_service import OntologyService
from ..core.errors import handle_result
from ..database import SessionLocal

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

from ..dependencies import get_db, get_ontology_service, get_webhook_service

@router.post(
    "", 
    response_model=schemas.WebhookResponse, 
    status_code=201,
    summary="注册新 Webhook"
)
async def create_webhook(
    webhook: schemas.WebhookCreate,
    service: WebhookService = Depends(get_webhook_service)
):
    result = service.create_webhook(webhook)
    return handle_result(result)

@router.get(
    "", 
    response_model=schemas.PaginatedWebhookResponse,
    summary="获取 Webhook 列表"
)
def list_webhooks(
    skip: int = 0, 
    limit: int = 100,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_webhooks(skip, limit)

@router.delete(
    "/{id}", 
    status_code=204,
    summary="删除 Webhook"
)
def delete_webhook(
    id: str,
    service: WebhookService = Depends(get_webhook_service)
):
    service.delete_webhook(id)
    return None

@router.put(
    "/{id}", 
    response_model=schemas.WebhookResponse,
    summary="更新 Webhook 配置"
)
def update_webhook(
    id: str,
    webhook: schemas.WebhookCreate,
    service: WebhookService = Depends(get_webhook_service)
):
    result = service.update_webhook(id, webhook)
    return handle_result(result)

@router.get(
    "/{id}/logs", 
    response_model=schemas.PaginatedWebhookDeliveryResponse,
    summary="获取 Webhook 交付日志"
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

@router.post(
    "/{id}/ping",
    summary="连通性测试 (Ping)"
)
async def ping_webhook(
    id: str,
    service: WebhookService = Depends(get_webhook_service)
):
    result = await service.ping_webhook(id)
    return handle_result(result)

from ..core.results import ServiceResult

@router.post(
    "/push/{id}",
    summary="手动触发 Webhook 推送",
    tags=["Webhooks"]
)
async def push_ontology_to_webhook(
    id: str,
    webhook_id: str = Query(..., description="目标 Webhook ID"),
    background_tasks: BackgroundTasks = None,
    service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    package = service.onto_repo.get_package(id)
    if not package:
        return handle_result(ServiceResult.not_found("本体包不存在"))
        
    zip_path = service.get_source_zip_path(package.id)
    push_result = await webhook_service.trigger_subscription(package, webhook_id, background_tasks, zip_path, sync=True)
    result_data = handle_result(push_result)
    
    return {
        "status": "pushed", 
        "package": package.code, 
        "version": package.version, 
        "target": webhook_id,
        "delivery_result": result_data
    }

@router.get(
    "/subscriptions/by-code/{code}",
    summary="获取本体订阅详情",
    tags=["Webhooks"]
)
def get_ontology_subscriptions(
    code: str,
    service: WebhookService = Depends(get_webhook_service)
):
    return service.get_subscription_status(name=None, code=code)

@router.get(
    "/deliveries/{id}",
    summary="查询本体交付历史",
    tags=["Webhooks"]
)
def get_ontology_deliveries(
    id: str,
    onto_service: OntologyService = Depends(get_ontology_service),
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    pkg_result = onto_service.get_ontology_detail(id)
    package = handle_result(pkg_result)
    return webhook_service.get_ontology_delivery_status(id, package.code)
