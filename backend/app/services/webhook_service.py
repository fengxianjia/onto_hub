import logging
import json
from typing import List, Optional
from fastapi import HTTPException
from ..repositories.webhook_repo import WebhookRepository
from .. import schemas, utils

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self, repo: WebhookRepository):
        self.repo = repo

    def create_webhook(self, webhook_in: schemas.WebhookCreate) -> schemas.WebhookResponse:
        return self.repo.create_webhook(webhook_in)

    def get_webhooks(self, skip: int = 0, limit: int = 100) -> List[schemas.WebhookResponse]:
        return self.repo.list_webhooks(skip, limit)

    def delete_webhook(self, webhook_id: str):
        self.repo.delete_webhook(webhook_id)

    def update_webhook(self, webhook_id: str, update_in: schemas.WebhookCreate) -> schemas.WebhookResponse:
        webhook = self.repo.update_webhook(webhook_id, update_in)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return webhook

    def get_logs_by_webhook(self, webhook_id: str, skip: int = 0, limit: int = 20):
        return self.repo.get_logs_by_webhook(webhook_id, skip, limit)

    def get_logs_by_ontology(self, ontology_name: str, skip: int = 0, limit: int = 50):
        deliveries = self.repo.get_logs_by_ontology(ontology_name, skip, limit)
        results = []
        for delivery, wh_name in deliveries:
            d_dict = {c.name: getattr(delivery, c.name) for c in delivery.__table__.columns}
            d_dict["webhook_name"] = wh_name
            results.append(d_dict)
        return results

    def get_subscription_status(self, name: str = None, code: str = None) -> List[dict]:
        # Logic from manager.py moved here
        # We fetch all "ontology.activated" webhooks and then filter in memory or via repo
        target_code = code

        # Fetch webhooks that match EITHER name OR code (or Global)
        # Note: repo.get_webhooks_by_event uses "ontology_filter" column.
        # Frontend ensures ontology_filter stores CODE.
        # So we theoretically only need ontology_code=target_code.
        # But to be safe and compatible with how repo works (OR condition), 
        # we can just pass ontology_code.
        
        webhooks = self.repo.get_webhooks_by_event(
            "ontology.activated", 
            ontology_code=target_code
        )
        
        results = []
        for wh in webhooks:
            # Check latest delivery using CODE only.
            # We assume all correct records are now stored with ontology_name=CODE.
            
            latest_success = None
            if target_code:
                 latest_success = self.repo.get_latest_success_delivery(wh.id, target_code)
            
            # If target_code is missing (shouldn't happen for this usage), we get nothing.
            
            version = None
            delivered_at = None
            if latest_success:
                try:
                    payload_data = json.loads(latest_success.payload)
                    version = payload_data.get("version")
                    delivered_at = latest_success.created_at
                except:
                    pass
            
            results.append({
                "webhook_id": wh.id,
                "webhook_name": wh.name,
                "target_url": wh.target_url,
                "latest_success_version": version,
                "delivered_at": delivered_at,
                "is_global": not wh.ontology_filter
            })
        return results

    async def ping_webhook(self, webhook_id: str) -> dict:
        webhook = self.repo.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
            
        payload = {
            "event": "ping",
            "webhook_id": webhook.id,
            "name": webhook.name,
            "timestamp": utils.time.time() 
        }
        
        try:
            # 现在是异步调用
            await utils.send_webhook_request(
                target_url=webhook.target_url,
                payload=payload,
                webhook_id=webhook.id,
                event_type="ping",
                save_log=True,
                secret_token=webhook.secret_token,
                ontology_name="SYSTEM_PING"
            )
            # 获取刚刚记录的日志
            deliveries = self.repo.get_logs_by_webhook(webhook.id, limit=1)
            if not deliveries:
                 return {"status": "FAILURE", "error_message": "No delivery log found"}
            
            delivery = deliveries[0]
            return {
                "status": delivery.status,
                "response_status": delivery.response_status,
                "error_message": delivery.error_message
            }
        except Exception as e:
            return {"status": "FAILURE", "error_message": str(e)}
            
        payload = {
            "event": "ping",
            "webhook_id": webhook.id,
            "name": webhook.name,
            "timestamp": utils.time.time() 
        }
        
        try:
            # 现在是异步调用
            await utils.send_webhook_request(
                target_url=webhook.target_url,
                payload=payload,
                webhook_id=webhook.id,
                event_type="ping",
                save_log=True,
                secret_token=webhook.secret_token,
                ontology_name="SYSTEM_PING"
            )
            # 获取刚刚记录的日志
            deliveries = self.repo.get_logs_by_webhook(webhook.id, limit=1)
            if not deliveries:
                 return {"status": "FAILURE", "error_message": "No delivery log found"}
            
            delivery = deliveries[0]
            return {
                "status": delivery.status,
                "response_status": delivery.response_status,
                "error_message": delivery.error_message
            }
        except Exception as e:
            return {"status": "FAILURE", "error_message": str(e)}

    def broadcast_event(self, event_type: str, payload: dict, ontology_name: str, background_tasks, file_path: str = None):
        """Find matching webhooks and add broadcast task to background_tasks."""
        webhooks = self.repo.get_webhooks_by_event(event_type, ontology_name=ontology_name)
        
        webhook_requests = []
        for wh in webhooks:
            webhook_requests.append({
                "target_url": wh.target_url,
                "payload": payload,
                "webhook_id": wh.id,
                "event_type": event_type,
                "file_path": file_path,
                "secret_token": wh.secret_token,
                "ontology_name": ontology_name
            })

        if webhook_requests:
            background_tasks.add_task(utils.broadcast_webhook_requests, webhook_requests)
            logger.info(f"Queued {len(webhook_requests)} webhooks for event {event_type}")

    async def trigger_subscription(self, package, webhook_id: str, background_tasks, file_path: str = None, sync: bool = False):
        """手动触发单个订阅的推送"""
        webhook = self.repo.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        # 构造激活事件 payload
        payload = {
            "event": "ontology.activated",
            "package_id": package.id,
            "code": package.code,
            "name": package.name,
            "version": package.version,
            "is_active": package.is_active,
            "timestamp": utils.time.time() # Or datetime.utcnow()
        }
        
        # 复用 broadcast 的 task 逻辑
        request = {
            "target_url": webhook.target_url,
            "payload": payload,
            "webhook_id": webhook.id,
            "event_type": "ontology.activated",
            "file_path": file_path,
            "secret_token": webhook.secret_token,
            "ontology_name": package.code # Use Code 
        }
        
        if sync:
            # 同步执行 (即使在 async def 中也是 await)
            result = await utils.send_webhook_request(**request)
            return result
        else:
            background_tasks.add_task(utils.broadcast_webhook_requests, [request])
            return {"status": "queued"}

    def get_ontology_delivery_status(self, package_id: str, ontology_name: str = None) -> List[dict]:
        """准确聚合特定本体版本的推送状态"""
        # 1. 获取针对该事件及其本体过滤器的所有已激活 Webhook
        # 必须传入 ontology_name，否则会包含不相关的 Webhook，导致永远显示 PENDING
        webhooks = self.repo.get_webhooks_by_event("ontology.activated", ontology_name=ontology_name)
        
        # 2. 获取该包的所有推送记录
        deliveries = self.repo.get_deliveries_by_package_id(package_id)
        delivery_map = {d.webhook_id: d for d in deliveries}
        
        # 3. 组装结果
        results = []
        for wh in webhooks:
            delivery = delivery_map.get(wh.id)
            item = {
                "webhook_id": wh.id,
                "webhook_name": wh.name,
                "target_url": wh.target_url,
                "status": "PENDING",
                "response_status": None,
                "error_message": None,
                "delivered_at": None
            }
            if delivery:
                item["status"] = delivery.status
                item["response_status"] = delivery.response_status
                item["error_message"] = delivery.error_message
                item["delivered_at"] = delivery.created_at # 对应前端需要的字段
                
            results.append(item)
        return results

    def get_in_use_package_ids(self, ontology_code: str) -> List[str]:
        """
        获取特定本体编码下正在被 Webhook 使用的包 ID 列表。
        正在使用指：在该 Webhook 下最后一次成功推送的版本。
        """
        webhooks = self.repo.get_webhooks_by_event("ontology.activated", ontology_code=ontology_code)
        in_use_ids = []
        for wh in webhooks:
            latest = self.repo.get_latest_success_delivery(wh.id, ontology_code)
            if latest and latest.payload:
                try:
                    payload_data = json.loads(latest.payload)
                    package_id = payload_data.get("id") or payload_data.get("package_id")
                    if package_id:
                        in_use_ids.append(package_id)
                except:
                    pass
        return list(set(in_use_ids))
