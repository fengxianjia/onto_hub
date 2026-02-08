from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
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

@router.get("/", response_model=List[schemas.ParsingTemplateResponse])
def list_templates(
    skip: int = 0, 
    limit: int = 100,
    service: TemplateService = Depends(get_template_service)
):
    return service.list_templates(skip, limit)

@router.post("/", response_model=schemas.ParsingTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template: schemas.ParsingTemplateCreate,
    service: TemplateService = Depends(get_template_service)
):
    return service.create_template(template)

@router.get("/{template_id}", response_model=schemas.ParsingTemplateResponse)
def get_template(
    template_id: str,
    service: TemplateService = Depends(get_template_service)
):
    return service.get_template(template_id)

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    service: TemplateService = Depends(get_template_service)
):
    service.delete_template(template_id)
    return None

@router.put("/{template_id}", response_model=schemas.ParsingTemplateResponse)
def update_template(
    template_id: str,
    template: schemas.ParsingTemplateCreate,
    service: TemplateService = Depends(get_template_service)
):
    return service.update_template(template_id, template)
