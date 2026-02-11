from fastapi import APIRouter, Depends, UploadFile, File, Query, BackgroundTasks, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, UTC

from .. import schemas, models, utils
from ..services.ontology_service import OntologyService
from ..services.webhook_service import WebhookService
from ..tasks import parse_ontology_task
from ..core.errors import handle_result
from ..database import SessionLocal

router = APIRouter(prefix="/api/ontologies", tags=["Ontologies"])

from ..dependencies import get_db, get_ontology_service, get_webhook_service

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
        ontology_name=package.code,
        background_tasks=background_tasks,
        file_path=service.get_source_zip_path(package.id),
        db=service.onto_repo.db
    )

@router.post(
    "", 
    response_model=schemas.OntologyPackageResponse, 
    status_code=201,
    summary="创建/上传本体新版本"
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
    
    matching_webhooks = webhook_service.repo.get_webhooks_by_event("ontology.activated", ontology_name=code)
    subscriber_count = len(matching_webhooks)

    if auto_push:
        _broadcast_activation(package, service, webhook_service, background_tasks)
    
    package_resp = schemas.OntologyPackageResponse.model_validate(package)
    package_resp.subscriber_count = subscriber_count

    final_template_id = template_id or package.template_id
    if final_template_id:
        background_tasks.add_task(parse_ontology_task, package.id, final_template_id, db=service.onto_repo.db)
        
    return package_resp

@router.post(
    "/{code}/versions", 
    response_model=schemas.OntologyPackageResponse, 
    status_code=201,
    summary="添加本体新版本"
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
    
    matching_webhooks = webhook_service.repo.get_webhooks_by_event("ontology.activated", ontology_name=code)
    subscriber_count = len(matching_webhooks)

    if auto_push:
        _broadcast_activation(package, service, webhook_service, background_tasks)
    
    package_resp = schemas.OntologyPackageResponse.model_validate(package)
    package_resp.subscriber_count = subscriber_count

    final_template_id = template_id or package.template_id
    if final_template_id:
        background_tasks.add_task(parse_ontology_task, package.id, final_template_id, db=service.onto_repo.db)
        
    return package_resp

@router.patch(
    "/{code}", 
    response_model=schemas.OntologyPackageResponse,
    summary="更新本体元数据"
)
async def update_ontology_metadata(
    code: str,
    series_in: schemas.OntologySeriesUpdate,
    service: OntologyService = Depends(get_ontology_service)
):
    result = await service.update_ontology_series(code, series_in)
    series = handle_result(result)
    
    latest_version = service.onto_repo.get_latest_version(code)
    package = service.onto_repo.get_active_package_by_code(code)
    if not package:
        pkg_list, _ = service.onto_repo.list_packages(latest_version, limit=1)
        package = pkg_list[0] if pkg_list else None
    
    if not package:
         raise HTTPException(status_code=404, detail="No versions found for this ontology")
         
    return package

@router.post(
    "/packages/{package_id}/reparse", 
    response_model=schemas.OntologyPackageResponse,
    summary="重新解析本体 (异步)"
)
async def reparse_ontology(
    package_id: str,
    background_tasks: BackgroundTasks,
    req: schemas.OntologyReparseRequest = None,
    service: OntologyService = Depends(get_ontology_service)
):
    template_id = req.template_id if req else None
    result = await service.reparse_ontology_package(package_id, template_id)
    final_template_id = handle_result(result)
    
    background_tasks.add_task(parse_ontology_task, package_id, final_template_id, db=service.onto_repo.db)
    return {"message": "Parsing task triggered", "template_id": final_template_id}

@router.get(
    "", 
    response_model=schemas.PaginatedOntologyResponse,
    summary="获取本体系列列表"
)
def get_ontologies(
    skip: int = 0, 
    limit: int = 100, 
    name: str = None,
    code: str = None,
    service: OntologyService = Depends(get_ontology_service)
):
    return service.list_ontologies(skip, limit, name, code, all_versions=False)

@router.get(
    "/{code}/versions", 
    response_model=schemas.PaginatedOntologyResponse,
    summary="列出本体所有版本历史"
)
def get_ontology_versions(
    code: str,
    skip: int = 0,
    limit: int = 100,
    service: OntologyService = Depends(get_ontology_service)
):
    return service.list_versions(code, skip, limit)

@router.get(
    "/{code}/versions/{version}/download",
    summary="下载指定版本的原始 ZIP 包"
)
async def download_ontology_version(
    code: str,
    version: int,
    service: OntologyService = Depends(get_ontology_service)
):
    from fastapi.responses import FileResponse
    result = service.get_version_package_path(code, version)
    file_path = handle_result(result)
    
    filename = f"{code}_v{version}.zip"
    return FileResponse(
        path=file_path, 
        filename=filename,
        media_type="application/zip"
    )

@router.post(
    "/{id}/activate",
    summary="激活本体特定版本"
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
        ontology_name=package.code,
        background_tasks=background_tasks,
        file_path=service.get_source_zip_path(package.id)
    )
        
    return {"status": "activated", "version": package.version}

@router.delete(
    "/{id}", 
    status_code=204,
    summary="删除单个本体版本"
)
def delete_ontology_version(
    id: str,
    service: OntologyService = Depends(get_ontology_service)
):
    result = service.delete_version(id)
    handle_result(result)
    return None

@router.delete(
    "/by-code/{code}", 
    status_code=204,
    summary="删除整个本体系列"
)
def delete_ontology_series(
    code: str,
    service: OntologyService = Depends(get_ontology_service)
):
    result = service.delete_ontology_series(code)
    handle_result(result)
    return None

@router.get(
    "/compare", 
    response_model=schemas.OntologyComparisonResponse,
    summary="差异化对比两个本体版本"
)
async def compare_ontologies(
    base_id: str = Query(..., description="基准版本ID"),
    target_id: str = Query(..., description="目标版本ID"),
    service: OntologyService = Depends(get_ontology_service)
):
    result = await service.compare_packages(base_id, target_id)
    return handle_result(result)

@router.get(
    "/{id}", 
    response_model=schemas.OntologyPackageDetailResponse,
    summary="获取本体包详细信息"
)
def get_ontology_detail(
    id: str,
    service: OntologyService = Depends(get_ontology_service)
):
    result = service.get_ontology_detail(id)
    return handle_result(result)

@router.get(
    "/{id}/files",
    summary="读取包内特定文件内容"
)
def read_ontology_file(
    id: str,
    path: str = Query(..., description="文件相对路径"),
    service: OntologyService = Depends(get_ontology_service)
):
    result = service.get_file_content(id, path)
    return {"content": handle_result(result)}

@router.get(
    "/{id}/graph", 
    response_model=schemas.OntologyGraphResponse,
    summary="获取本体关联图谱"
)
def get_ontology_graph(
    id: str,
    db: Session = Depends(get_db)
):
    entities = db.query(models.OntologyEntity).filter(models.OntologyEntity.package_id == id).all()
    relations = db.query(models.OntologyRelation).filter(models.OntologyRelation.package_id == id).all()
    
    return {
        "nodes": entities,
        "links": relations
    }

@router.get(
    "/{id}/entities", 
    response_model=List[schemas.OntologyEntityResponse],
    summary="分页获取本体实体列表"
)
def get_ontology_entities(
    id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return db.query(models.OntologyEntity).filter(models.OntologyEntity.package_id == id).offset(skip).limit(limit).all()

@router.get(
    "/{id}/relations", 
    response_model=schemas.PaginatedOntologyRelationResponse,
    summary="分页获取本体关系列表"
)
def get_ontology_relations(
    id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: OntologyService = Depends(get_ontology_service)
):
    return service.list_relations(id, skip, limit)
