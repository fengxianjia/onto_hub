from typing import List, Optional
from fastapi import HTTPException
from ..repositories.template_repo import TemplateRepository
from .. import schemas

class TemplateService:
    def __init__(self, template_repo: TemplateRepository):
        self.template_repo = template_repo

    def list_templates(self, skip: int = 0, limit: int = 100) -> List[schemas.ParsingTemplateResponse]:
        templates = self.template_repo.list_templates(skip, limit)
        return [schemas.ParsingTemplateResponse.model_validate(t) for t in templates]

    def get_template(self, template_id: str) -> schemas.ParsingTemplateResponse:
        template = self.template_repo.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return schemas.ParsingTemplateResponse.model_validate(template)

    def create_template(self, template: schemas.ParsingTemplateCreate) -> schemas.ParsingTemplateResponse:
        if self.template_repo.get_template_by_name(template.name):
            raise HTTPException(status_code=400, detail="Template with this name already exists")
        
        # Validate JSON rules logic here if needed
        # import json
        # try:
        #    json.loads(template.rules)
        # except:
        #    raise HTTPException(status_code=400, detail="Invalid JSON format for rules")

        new_template = self.template_repo.create_template(template)
        return schemas.ParsingTemplateResponse.model_validate(new_template)
    
    def delete_template(self, template_id: str):
        if not self.template_repo.delete_template(template_id):
             raise HTTPException(status_code=400, detail="Cannot delete template: it is in use or does not exist")
    
    def update_template(self, template_id: str, template: schemas.ParsingTemplateCreate) -> schemas.ParsingTemplateResponse:
        updated = self.template_repo.update_template(template_id, template)
        if not updated:
            raise HTTPException(status_code=404, detail="Template not found")
        return schemas.ParsingTemplateResponse.model_validate(updated)
