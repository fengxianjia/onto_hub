import os
import shutil
import zipfile
import logging
import json
import aiofiles
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from typing import List, Optional

from ..repositories.ontology_repo import OntologyRepository
from ..repositories.webhook_repo import WebhookRepository
from ..core.events import dispatcher
from .. import models, schemas, utils

logger = logging.getLogger(__name__)

# 配置存储路径: app/services/ontology_service.py -> backend/data/ontology_storage
BASE_STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
    "data", 
    "ontohub_storage"
)
os.makedirs(BASE_STORAGE_DIR, exist_ok=True)

class OntologyService:
    def __init__(self, onto_repo: OntologyRepository, webhook_repo: WebhookRepository, webhook_service: 'WebhookService' = None):
        self.onto_repo = onto_repo
        self.webhook_repo = webhook_repo
        self.webhook_service = webhook_service

    def _get_storage_path(self, package_id: str) -> str:
        return os.path.join(BASE_STORAGE_DIR, package_id)

    def _safe_extract(self, zip_ref: zipfile.ZipFile, extract_path: str):
        for member in zip_ref.namelist():
            filename = os.path.basename(member)
            if not filename:
                continue
            
            target_path = os.path.normpath(os.path.join(extract_path, member))
            if not target_path.startswith(os.path.normpath(extract_path)):
                logger.warning(f"Zip Slip attempt blocked: {member}")
                continue
            
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with zip_ref.open(member) as source, open(target_path, "wb") as target:
                shutil.copyfileobj(source, target)

    async def create_ontology(self, file: UploadFile) -> models.OntologyPackage:
        # Simplified process based on manager.py
        temp_zip = f"temp_{datetime.now().timestamp()}.zip"
        async with aiofiles.open(temp_zip, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        ontology_name = file.filename # 保留完整名称 (e.g. 业务对象.zip)
        version = self.onto_repo.get_latest_version(ontology_name) + 1
        
        # Create record first to get ID
        db_package = self.onto_repo.create_package(name=ontology_name, version=version)
        storage_path = self._get_storage_path(db_package.id)
        os.makedirs(storage_path, exist_ok=True)

        # Save the zip file itself for future webhook broadcasts
        final_zip_path = self.get_source_zip_path(db_package.id)
        shutil.copy2(temp_zip, final_zip_path)

        try:
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                self._safe_extract(zip_ref, storage_path)
                
            # Scan and batch create file records
            file_records = []
            for root, dirs, files in os.walk(storage_path):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    rel_path = os.path.relpath(fpath, storage_path).replace("\\", "/")
                    fsize = os.path.getsize(fpath)
                    
                    preview = None
                    if fname.endswith(('.md', '.txt', '.json')):
                        try:
                            with open(fpath, 'r', encoding='utf-8') as f:
                                preview = f.read(1000)
                        except:
                            pass
                    
                    file_records.append({
                        "package_id": db_package.id,
                        "file_path": rel_path,
                        "file_size": fsize,
                        "content_preview": preview
                    })
            
            # Batch creation in repo
            self.onto_repo.create_files_batch(file_records)

            # Auto activate on upload
            self.activate_ontology(db_package.id)
            
            return db_package
        finally:
            if os.path.exists(temp_zip):
                os.remove(temp_zip)

    def activate_ontology(self, package_id: str) -> models.OntologyPackage:
        package = self.onto_repo.get_package(package_id)
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # 激活前先确保此本体包的基础信息已同步
        self.onto_repo.set_active_version(package.name, package_id)
        
        # 触发本地事件 (同步触发，但由于业务简单，暂不使用异步)
        dispatcher.dispatch("ontology.activated", {
            "name": package.name,
            "version": package.version,
            "package_id": package.id
        })
        
        return package

    def list_ontologies(self, skip: int = 0, limit: int = 100, name: str = None, all_versions: bool = False):
        packages = self.onto_repo.list_packages(skip, limit, name, all_versions)
        
        # Convert to Pydantic models immediately to ensure we can modify fields
        results = [schemas.OntologyPackageResponse.model_validate(pkg) for pkg in packages]

        # 如果查询的是版本列表，需要增加安全性标记
        if name and all_versions:
            in_use_ids = self.webhook_service.get_in_use_package_ids(name)
            for pkg in results:
                if pkg.is_active:
                    pkg.is_deletable = False
                    pkg.deletable_reason = "当前版本已启用"
                elif pkg.id in in_use_ids:
                    pkg.is_deletable = False
                    pkg.deletable_reason = "该版本正在 Webhook 订阅中使用"
                else:
                    pkg.is_deletable = True
                    pkg.deletable_reason = None
        return results

    def get_ontology_detail(self, package_id: str):
        package = self.onto_repo.get_package(package_id)
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Convert to Pydantic model
        result = schemas.OntologyPackageDetailResponse.model_validate(package)

        # 详情页同样补充安全性标记
        in_use_ids = self.webhook_service.get_in_use_package_ids(package.name)
        if result.is_active:
            result.is_deletable = False
            result.deletable_reason = "当前版本已启用"
        elif result.id in in_use_ids:
            result.is_deletable = False
            result.deletable_reason = "该版本正在 Webhook 订阅中使用"
        else:
            result.is_deletable = True
            result.deletable_reason = None

        return result

    def get_file_content(self, package_id: str, relative_path: str) -> str:
        # Check storage
        file_path = os.path.join(self._get_storage_path(package_id), relative_path)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

    def delete_ontology(self, package_id: str):
        package = self.onto_repo.get_package(package_id)
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
            
        # 安全校验：Active 的不能删
        if package.is_active:
            raise HTTPException(status_code=400, detail="正在启用的版本不能删除")
            
        # 安全校验：订阅者正在使用的不能删
        in_use_ids = self.webhook_service.get_in_use_package_ids(package.name)
        if package.id in in_use_ids:
            raise HTTPException(status_code=400, detail="该版本正在 Webhook 订阅中使用，不能删除")

        self.onto_repo.delete_package(package_id)
        storage_path = self._get_storage_path(package_id)
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)

    def get_source_zip_path(self, package_id: str) -> str:
        # This belongs more to a StorageService but we'll put it here for now
        # Actually manager.py had a simple logic for this
        return os.path.join(BASE_STORAGE_DIR, f"{package_id}.zip") # Wait, manager.py just returned a path
