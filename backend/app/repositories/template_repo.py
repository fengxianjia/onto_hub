from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas

class TemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_template(self, template_id: str) -> Optional[models.ParsingTemplate]:
        return self.db.query(models.ParsingTemplate).filter(models.ParsingTemplate.id == template_id).first()

    def get_template_by_name(self, name: str) -> Optional[models.ParsingTemplate]:
        return self.db.query(models.ParsingTemplate).filter(models.ParsingTemplate.name == name).first()

    def list_templates(self, skip: int = 0, limit: int = 100) -> List[models.ParsingTemplate]:
        return self.db.query(models.ParsingTemplate).offset(skip).limit(limit).all()

    def create_template(self, template: schemas.ParsingTemplateCreate) -> models.ParsingTemplate:
        db_template = models.ParsingTemplate(
            name=template.name,
            description=template.description,
            rules=template.rules
        )
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        return db_template

    def delete_template(self, template_id: str) -> bool:
        db_template = self.get_template(template_id)
        if db_template:
            # Check if used by any packages
            if db_template.packages:
                return False # Cannot delete
                
            self.db.delete(db_template)
            self.db.commit()
            return True
        return False
        
    def update_template(self, template_id: str, template: schemas.ParsingTemplateCreate) -> Optional[models.ParsingTemplate]:
        db_template = self.get_template(template_id)
        if not db_template:
            return None
            
        db_template.name = template.name
        db_template.description = template.description
        db_template.rules = template.rules
        
        self.db.commit()
        self.db.refresh(db_template)
        return db_template
