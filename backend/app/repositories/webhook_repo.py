from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional, Tuple
from .. import models, schemas

class WebhookRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_webhook(self, webhook_in: schemas.WebhookCreate) -> models.Webhook:
        # Check idempotency
        existing = self.db.query(models.Webhook).filter(
            models.Webhook.target_url == webhook_in.target_url,
            models.Webhook.event_type == webhook_in.event_type
        ).first()
        
        if existing:
            return existing

        db_webhook = models.Webhook(
            name=webhook_in.name or "Webhook",
            target_url=webhook_in.target_url,
            event_type=webhook_in.event_type,
            ontology_code=webhook_in.ontology_code,
            secret_token=webhook_in.secret_token
        )
        self.db.add(db_webhook)
        self.db.commit()
        self.db.refresh(db_webhook)
        return db_webhook

    def get_webhook(self, webhook_id: str) -> Optional[models.Webhook]:
        return self.db.query(models.Webhook).filter(models.Webhook.id == webhook_id).first()

    def get_webhook_by_name(self, name: str) -> Optional[models.Webhook]:
        return self.db.query(models.Webhook).filter(models.Webhook.name == name).first()

    def list_webhooks(self, skip: int = 0, limit: int = 100) -> Tuple[List[models.Webhook], int]:
        query = self.db.query(models.Webhook)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def delete_webhook(self, webhook_id: str):
        webhook = self.get_webhook(webhook_id)
        if webhook:
            self.db.delete(webhook)
            self.db.commit()

    def update_webhook(self, webhook_id: str, update_in: schemas.WebhookCreate) -> Optional[models.Webhook]:
        webhook = self.get_webhook(webhook_id)
        if not webhook:
            return None
        
        webhook.name = update_in.name or webhook.name
        webhook.target_url = update_in.target_url
        webhook.event_type = update_in.event_type
        webhook.ontology_code = update_in.ontology_code
        webhook.secret_token = update_in.secret_token
        
        self.db.commit()
        self.db.refresh(webhook)
        return webhook

    def get_webhooks_by_event(self, event_type: str, ontology_code: str = None) -> List[models.Webhook]:
        query = self.db.query(models.Webhook).filter(models.Webhook.event_type == event_type)
        
        # 1. 全局 Webhook (过滤器为空)
        # 2. 过滤器匹配本体编码
        
        conditions = [
            models.Webhook.ontology_code == None,
            models.Webhook.ontology_code == ""
        ]
        
        if ontology_code:
            conditions.append(models.Webhook.ontology_code == ontology_code)
            
        query = query.filter(or_(*conditions))
        return query.all()

    def create_delivery(self, 
        webhook_id: str, 
        event_type: str, 
        ontology_code: str, 
        payload: str, 
        status: str, 
        response_status: int = None, 
        error_message: str = None
    ) -> models.WebhookDelivery:
        db_delivery = models.WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            ontology_code=ontology_code,
            payload=payload,
            status=status,
            response_status=response_status,
            error_message=error_message
        )
        self.db.add(db_delivery)
        self.db.commit()
        return db_delivery

    def get_logs_by_ontology(self, ontology_code: str, skip: int = 0, limit: int = 50) -> List[Tuple[models.WebhookDelivery, str]]:
        return self.db.query(models.WebhookDelivery, models.Webhook.name)\
            .join(models.Webhook, models.WebhookDelivery.webhook_id == models.Webhook.id)\
            .filter(models.WebhookDelivery.ontology_code == ontology_code)\
            .order_by(desc(models.WebhookDelivery.created_at))\
            .offset(skip).limit(limit).all()

    def get_logs_by_webhook(self, webhook_id: str, ontology_code: str = None, status: str = None, skip: int = 0, limit: int = 20) -> Tuple[List[Tuple[models.WebhookDelivery, str]], int]:
        query = self.db.query(models.WebhookDelivery, models.Webhook.name)\
            .join(models.Webhook, models.WebhookDelivery.webhook_id == models.Webhook.id)\
            .filter(models.WebhookDelivery.webhook_id == webhook_id)
        
        if ontology_code:
             query = query.filter(models.WebhookDelivery.ontology_code.contains(ontology_code))
        
        if status:
            query = query.filter(models.WebhookDelivery.status == status)
             
        total = query.count()
        items = query.order_by(desc(models.WebhookDelivery.created_at))\
            .offset(skip).limit(limit).all()
        return items, total

    def get_latest_success_delivery(self, webhook_id: str, ontology_code: str) -> Optional[models.WebhookDelivery]:
        return self.db.query(models.WebhookDelivery)\
            .filter(models.WebhookDelivery.webhook_id == webhook_id)\
            .filter(models.WebhookDelivery.status == "SUCCESS")\
            .filter(models.WebhookDelivery.ontology_code == ontology_code)\
            .order_by(desc(models.WebhookDelivery.created_at))\
            .first()

    def get_deliveries_by_package_id(self, package_id: str) -> List[models.WebhookDelivery]:
        # Simple string search as in legacy manager.py
        search_key = f'"{package_id}"'
        return self.db.query(models.WebhookDelivery)\
            .filter(models.WebhookDelivery.event_type == "ontology.activated")\
            .filter(models.WebhookDelivery.payload.contains(search_key))\
            .all()

    def get_name_by_code(self, code: str) -> Optional[str]:
        # 我们使用 series_code 来匹配包
        pkg = self.db.query(models.OntologyPackage)\
            .filter(models.OntologyPackage.series_code == code)\
            .order_by(desc(models.OntologyPackage.version))\
            .first()
        return pkg.name if pkg else None
