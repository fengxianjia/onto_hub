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
    def subscribe(event_name: str, callback: Callable, ontology_filter: str = None):
        """
        订阅本地事件
        :param event_name: 事件名称, 如 'ontology.activated'
        :param callback: 回调函数, 接收 payload 字典
        :param ontology_filter: 可选, 仅订阅指定名称的本体
        """
        # 使用解耦后的 dispatcher
        dispatcher.subscribe(event_name, callback, ontology_filter)
        logger.info(f"SDK Subscriber registered for {event_name} (filter: {ontology_filter})")

    @staticmethod
    def get_active_ontology(api_base_url: str, name: str):
        """
        从远程或本地 API 获取当前激活的本体元数据
        """
        try:
            response = requests.get(f"{api_base_url}/api/ontologies", params={"name": name})
            if response.ok:
                data = response.json()
                return data[0] if data else None
        except Exception as e:
            logger.error(f"SDK failed to fetch active ontology: {e}")
        return None
