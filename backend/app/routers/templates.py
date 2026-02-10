from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..core.errors import BusinessException, BusinessCode, handle_result
from ..repositories.template_repo import TemplateRepository
from ..services.template_service import TemplateService

router = APIRouter(
    prefix="/api/templates",
    tags=["Templates"],
    responses={404: {"description": "Not found"}},
)

def get_template_service(db: Session = Depends(get_db)) -> TemplateService:
    repo = TemplateRepository(db)
    return TemplateService(repo)

@router.get(
    "/", 
    response_model=List[schemas.ParsingTemplateResponse],
    summary="获取解析模板列表",
    description="获取系统中所有已定义的解析模板及其具体规则配置。"
)
def list_templates(
    skip: int = 0, 
    limit: int = 100,
    service: TemplateService = Depends(get_template_service)
):
    return service.list_templates(skip, limit)

@router.post(
    "/", 
    response_model=schemas.ParsingTemplateResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="创建解析模板",
    description="定义一套新的本体解析规则，包括实体名称来源、映射策略及正则提取模式。"
)
def create_template(
    template: schemas.ParsingTemplateCreate,
    service: TemplateService = Depends(get_template_service)
):
    result = service.create_template(template)
    return handle_result(result)

@router.get(
    "/{template_id}", 
    response_model=schemas.ParsingTemplateResponse,
    summary="获取模板详情",
    description="通过 UUID 获取特定解析模板的详细配置信息。"
)
def get_template(
    template_id: str,
    service: TemplateService = Depends(get_template_service)
):
    result = service.get_template(template_id)
    return handle_result(result)

@router.delete(
    "/{template_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除解析模板",
    description="物理删除指定的模板记录。注意：如果该模板已被本体版本引用，可能会导致相关解析逻辑不可用。"
)
def delete_template(
    template_id: str,
    service: TemplateService = Depends(get_template_service)
):
    result = service.delete_template(template_id)
    handle_result(result)
    return None

@router.put(
    "/{template_id}", 
    response_model=schemas.ParsingTemplateResponse,
    summary="更新解析模板",
    description="修改现有模板的名称、描述或核心解析规则逻辑。"
)
def update_template(
    template_id: str,
    template: schemas.ParsingTemplateCreate,
    service: TemplateService = Depends(get_template_service)
):
    result = service.update_template(template_id, template)
    return handle_result(result)
