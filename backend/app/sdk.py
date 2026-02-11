import logging
import requests
from typing import Callable, Optional
from .core.events import dispatcher

logger = logging.getLogger(__name__)

class OntologySDK:
    """
    针对本地集成的 SDK。
    支持在同一进程内订阅本体变更事件。
    """
    
    @staticmethod
    def subscribe(event_name: str, callback: Callable, ontology_code: str = None):
        """
        订阅本地事件
        :param event_name: 事件名称, 如 'ontology.activated'
        :param callback: 回调函数, 接收 payload 字典
        :param ontology_code: 可选, 仅订阅指定编码的本体
        """
        # 使用解耦后的 dispatcher
        dispatcher.subscribe(event_name, callback, ontology_code)
        logger.info(f"SDK Subscriber registered for {event_name} (filter: {ontology_code})")

    @staticmethod
    def get_ontologies(api_base_url: str, skip: int = 0, limit: int = 100):
        """
        获取本体系列列表
        """
        try:
            response = requests.get(f"{api_base_url}/api/ontologies", params={"skip": skip, "limit": limit})
            if response.ok:
                return response.json() # Returns {items, total}
        except Exception as e:
            logger.error(f"SDK failed to fetch ontologies: {e}")
        return {"items": [], "total": 0}

    @staticmethod
    def get_active_ontology(api_base_url: str, name: str):
        """
        从远程或本地 API 获取当前激活的本体元数据
        """
        try:
            response = requests.get(f"{api_base_url}/api/ontologies", params={"name": name})
            if response.ok:
                data = response.json()
                # data is { items: [], total: ... }
                items = data.get("items", [])
                return items[0] if items else None
        except Exception as e:
            logger.error(f"SDK failed to fetch active ontology: {e}")
    @staticmethod
    def get_file_content(api_base_url: str, package_id: str, file_path: str):
        """
        获取文件内容
        """
        try:
            # Re-use the client logic or API endpoint
            # API endpoint: /api/ontologies/{id}/files/{path}
            # But wait, does this endpoint exist?
            # Let's check main.py
            url = f"{api_base_url}/api/ontologies/{package_id}/files"
            response = requests.get(url, params={"path": file_path})
            if response.ok:
                return response.json().get("content", "")
        except Exception as e:
            logger.error(f"SDK failed to fetch file content: {e}")
        return ""
