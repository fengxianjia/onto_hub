from sqlalchemy.orm import Session
from fastapi import Depends
from .database import SessionLocal

def get_db():
    """数据库 Session 依赖项"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_webhook_service(db: Session = Depends(get_db)):
    """Webhook 业务服务依赖项"""
    from .repositories.webhook_repo import WebhookRepository
    from .services.webhook_service import WebhookService
    webhook_repo = WebhookRepository(db)
    return WebhookService(webhook_repo)

def get_ontology_service(
    db: Session = Depends(get_db), 
    webhook_service=Depends(get_webhook_service)
):
    """本体业务服务依赖项"""
    from .repositories.ontology_repo import OntologyRepository
    from .repositories.webhook_repo import WebhookRepository
    from .services.ontology_service import OntologyService
    onto_repo = OntologyRepository(db)
    webhook_repo = WebhookRepository(db)
    return OntologyService(onto_repo, webhook_repo, webhook_service)
