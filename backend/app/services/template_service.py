from typing import List, Optional
from ..repositories.template_repo import TemplateRepository
from .. import schemas
from ..core.results import ServiceResult, ServiceStatus
from ..core.errors import BusinessCode

class TemplateService:
    def __init__(self, template_repo: TemplateRepository):
        self.template_repo = template_repo

    def list_templates(self, skip: int = 0, limit: int = 100) -> List[schemas.ParsingTemplateResponse]:
        templates = self.template_repo.list_templates(skip, limit)
        return [schemas.ParsingTemplateResponse.model_validate(t) for t in templates]

    def get_template(self, template_id: str) -> ServiceResult[schemas.ParsingTemplateResponse]:
        template = self.template_repo.get_template(template_id)
        if not template:
             return ServiceResult.failure_result(
                 ServiceStatus.NOT_FOUND, 
                 "Template not found",
                 business_code=BusinessCode.TEMPLATE_NOT_FOUND
             )
        return ServiceResult.success_result(schemas.ParsingTemplateResponse.model_validate(template))

    def create_template(self, template: schemas.ParsingTemplateCreate) -> ServiceResult[schemas.ParsingTemplateResponse]:
        # Validation is now preferred in service for strict layering logic
        if self.template_repo.get_template_by_name(template.name):
            return ServiceResult.failure_result(
                ServiceStatus.DUPLICATE_NAME, 
                f"Template name '{template.name}' already exists.",
                business_code=BusinessCode.TEMPLATE_NAME_DUPLICATE
            )
            
        new_template = self.template_repo.create_template(template)
        return ServiceResult.success_result(schemas.ParsingTemplateResponse.model_validate(new_template))
    
    def delete_template(self, template_id: str) -> ServiceResult[None]:
        db_template = self.template_repo.get_template(template_id)
        if not db_template:
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND, 
                "Template not found",
                business_code=BusinessCode.TEMPLATE_NOT_FOUND
            )
            
        if db_template.packages:
            return ServiceResult.failure_result(
                ServiceStatus.RESOURCE_IN_USE, 
                "Template is in use and cannot be deleted",
                business_code=BusinessCode.RESOURCE_IN_USE
            )
            
        self.template_repo.delete_template(template_id)
        return ServiceResult.success_result()
    
    def update_template(self, template_id: str, template: schemas.ParsingTemplateCreate) -> ServiceResult[schemas.ParsingTemplateResponse]:
        updated = self.template_repo.update_template(template_id, template)
        if not updated:
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND, 
                "Template not found",
                business_code=BusinessCode.TEMPLATE_NOT_FOUND
            )
        return ServiceResult.success_result(schemas.ParsingTemplateResponse.model_validate(updated))
