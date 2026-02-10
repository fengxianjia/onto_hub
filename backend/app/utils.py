import httpx
import os
import logging
import json
import asyncio
import hmac
import hashlib
import time
from sqlalchemy.orm import Session
from . import models, database

logger = logging.getLogger(__name__)

async def _save_delivery_log(webhook_id, event_type, ontology_name, payload, status, response_status, error_message, db: Session = None):
    should_close = False
    if db is None:
        db = database.SessionLocal()
        should_close = True
        
    try:
        delivery = models.WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            ontology_name=ontology_name,
            payload=json.dumps(payload, ensure_ascii=False),
            status=status,
            response_status=response_status,
            error_message=error_message
        )
        db.add(delivery)
        db.commit()
    except Exception as db_e:
        logger.error(f"Failed to save webhook log: {db_e}")
    finally:
        if should_close:
            db.close()

async def send_webhook_request(
    target_url: str, 
    payload: dict, 
    webhook_id: str, 
    event_type: str, 
    file_path: str = None, 
    save_log: bool = True,
    secret_token: str = None,
    ontology_name: str = None,
    db: Session = None
):
    """
    异步发送 Webhook 请求并记录日志 (支持重试、签名、优化日志)
    """
    status = "FAILURE"
    response_status = None
    error_message = None
    max_retries = 3
    retry_delay = 1 # seconds

    # 1. 计算签名 (HMAC-SHA256)
    headers = {}
    if secret_token:
        payload_str = json.dumps(payload, ensure_ascii=False)
        signature = hmac.new(
            secret_token.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        headers['X-Hub-Signature-256'] = f"sha256={signature}"
        logger.info(f"Webhook signature generated for {target_url}")

    # 0. URL 清洗
    target_url = target_url.strip()
    if not target_url.startswith(("http://", "https://")):
        error_message = f"Invalid URL protocol: {target_url}"
        logger.error(error_message)
        # 记录失败日志并返回
        if save_log:
            await _save_delivery_log(webhook_id, event_type, ontology_name, payload, "FAILURE", None, error_message, db=db)
        return

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        # 2. 执行发送 (带异步重试逻辑)
        for attempt in range(max_retries):
            try:
                if file_path and os.path.exists(file_path):
                    # Multi-part file upload
                    with open(file_path, 'rb') as f:
                        files = {'file': (os.path.basename(file_path), f, 'application/zip')}
                        data = {'payload': json.dumps(payload, ensure_ascii=False)}
                        response = await client.post(target_url, data=data, files=files, headers=headers)
                else:
                    response = await client.post(target_url, json=payload, headers=headers)

                response_status = response.status_code
                if response.is_success:
                    status = "SUCCESS"
                    logger.info(f"Webhook sent successfully to {target_url} (Attempt {attempt+1})")
                    break
                else:
                    error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(f"Webhook failed (Attempt {attempt+1}): {error_message}")
            except Exception as e:
                error_message = str(e)
                logger.error(f"Error sending webhook (Attempt {attempt+1}): {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay) # 异步等待，不阻塞线程
                retry_delay *= 2 # 指数退避

        if save_log:
            await _save_delivery_log(
                webhook_id=webhook_id,
                event_type=event_type,
                ontology_name=ontology_name,
                payload=payload,
                status=status,
                response_status=response_status,
                error_message=error_message,
                db=db
            )
        
    return {
        "status": status,
        "response_status": response_status,
        "error_message": error_message
    }

async def broadcast_webhook_requests(requests_data: list):
    """
    真正的并发异步发送
    """
    logger.info(f"Broadcasting {len(requests_data)} webhooks asynchronously...")
    tasks = []
    for data in requests_data:
        tasks.append(send_webhook_request(**data))
    
    if tasks:
        # 并发执行所有请求
        await asyncio.gather(*tasks)
    logger.info("Broadcast completed.")
