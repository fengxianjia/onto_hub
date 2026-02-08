"""
OntoHub Python SDK
~~~~~~~~~~~~~~~~~~

这是一个为 OntoHub 提供便捷调用的 Python 客户端驱动。
它可以帮助外部 Python 应用（如 AI 模型服务、自动化脚本）通过 HTTP API
无缝集成本体管理功能，而无需手动编写复杂的接口调用代码。
"""

import requests
import os
from typing import List, Dict, Optional

class OntologyClient:
    """
    Ontology Management HTTP Client (SDK)
    
    适用于独立部署 (Docker/Microservice) 的项目。
    提供了本体上传、版本激活、Webhook 订阅及图谱获取等核心操作的封装。
    """

    def __init__(self, base_url: str):
        """
        :param base_url: 本体管理服务的地址，例如 "http://192.168.1.100:8000"
        """
        self.base_url = base_url.rstrip("/")

    def upload_ontology(self, file_path: str, code: str, name: str = None) -> Dict:
        """
        上传本体 ZIP 包 (创建新系列或新版本)
        :param file_path: ZIP 文件路径
        :param code: 本体唯一编码 (Series ID)
        :param name: 显示名称 (仅在创建新系列时需要)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Determine if we should use create (POST /api/ontologies) or add version (POST /api/ontologies/{code}/versions)
        # For simplicity in client, we might just try to create first, or expose two methods.
        # Let's align with the API: 
        # API 1: POST /api/ontologies (Create Series)
        # API 2: POST /api/ontologies/{code}/versions (Add Version)
        # But this client method is generic "upload". 
        # Let's use the `create_ontology` endpoint which is now filtered.
        # Logic: If name is provided, assume creating new series. If not, assume adding version.
        if name:
            return self.create_ontology(file_path, code, name)
        else:
            return self.add_version(file_path, code) 

    def create_ontology(self, file_path: str, code: str, name: str, template_id: str = None) -> Dict:
        """创建新的本体系列"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        url = f"{self.base_url}/api/ontologies"
        filename = os.path.basename(file_path)
        data = {"code": code, "name": name}
        if template_id:
            data["template_id"] = template_id
        
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/zip")}
            response = requests.post(url, data=data, files=files)
            
        response.raise_for_status()
        return response.json()

    def add_version(self, file_path: str, code: str, template_id: str = None) -> Dict:
        """添加新版本到现有系列"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        url = f"{self.base_url}/api/ontologies/{code}/versions"
        filename = os.path.basename(file_path)
        data = {}
        if template_id:
            data["template_id"] = template_id
        
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/zip")}
            response = requests.post(url, data=data, files=files)
            
        response.raise_for_status()
        return response.json()

    def get_ontologies(self, skip: int = 0, limit: int = 100, code: str = None) -> Dict:
        """
        获取本体系列列表 (Series List)
        :return: {"items": [...], "total": int}
        """
        url = f"{self.base_url}/api/ontologies"
        params = {"skip": skip, "limit": limit}
        if code:
            params["code"] = code
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_ontology_versions(self, code: str, skip: int = 0, limit: int = 100) -> Dict:
        """
        获取特定本体的历史版本列表
        :return: {"items": [...], "total": int}
        """
        url = f"{self.base_url}/api/ontologies/{code}/versions"
        params = {"skip": skip, "limit": limit}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def delete_ontology(self, ontology_id: str):
        """删除指定版本的本体"""
        url = f"{self.base_url}/api/ontologies/{ontology_id}"
        response = requests.delete(url)
        response.raise_for_status()

    def activate_ontology(self, ontology_id: str):
        """激活指定版本的本体"""
        url = f"{self.base_url}/api/ontologies/{ontology_id}/activate"
        response = requests.post(url)
        response.raise_for_status()
        return response.json()

    # --- Webhooks ---
    def subscribe_webhook(self, target_url: str, event_type: str = "ontology.activated", ontology_filter: str = None) -> Dict:
        """注册 Webhook"""
        url = f"{self.base_url}/api/webhooks"
        payload = {
            "target_url": target_url, 
            "event_type": event_type,
            "ontology_filter": ontology_filter
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def list_webhooks(self, skip: int = 0, limit: int = 100) -> Dict:
        """
        列出已注册的 Webhooks
        :return: {"items": [...], "total": int}
        """
        url = f"{self.base_url}/api/webhooks"
        params = {"skip": skip, "limit": limit}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def unsubscribe_webhook(self, webhook_id: str):
        """取消订阅"""
        url = f"{self.base_url}/api/webhooks/{webhook_id}"
        response = requests.delete(url)
        response.raise_for_status()

    # --- Templates & Graph ---
    def create_template(self, name: str, rules: dict) -> Dict:
        """创建解析模板"""
        url = f"{self.base_url}/api/templates/"
        import json
        payload = {
            "name": name,
            "rules": json.dumps(rules),
            "description": "Auto-created by client"
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_ontology_graph(self, ontology_id: str) -> Dict:
        """获取本体图谱"""
        url = f"{self.base_url}/api/ontologies/{ontology_id}/graph"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
