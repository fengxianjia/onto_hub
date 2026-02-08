import os
import shutil
import zipfile
import logging
import json
import aiofiles
import difflib
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from typing import List, Optional

from ..repositories.ontology_repo import OntologyRepository
from ..repositories.webhook_repo import WebhookRepository
from ..core.events import dispatcher
from .. import models, schemas, utils
from ..config import settings

logger = logging.getLogger(__name__)

# 配置存储路径: app/services/ontology_service.py -> backend/data/ontology_storage
BASE_STORAGE_DIR = settings.STORAGE_DIR
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

    async def create_ontology(self, file: UploadFile, code: str, custom_id: str = None, name: str = None, template_id: str = None) -> models.OntologyPackage:
        # Simplified process based on manager.py
        temp_zip = os.path.join(BASE_STORAGE_DIR, f"temp_{datetime.now().timestamp()}.zip")
        async with aiofiles.open(temp_zip, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # 1. Update/Create Series (Global Config)
        series = self.onto_repo.get_series(code)
        
        # If name is provided, use it (and update series). 
        # If not, try to use series name, or fallback to filename.
        final_name = name
        if not final_name:
            if series:
                final_name = series.name
            else:
                final_name = file.filename

        # If template_id provided, use it (and update default if user wants? For now, let's say uploading a version with template sets default if series is new)
        final_template_id = template_id
        if not final_template_id and series:
            final_template_id = series.default_template_id

        if not series:
            # Create new series
            series = self.onto_repo.create_series(code=code, name=final_name, default_template_id=final_template_id)
        else:
            # Update existing series metadata if new values provided
            # Only update if explicitly provided
            update_kwargs = {}
            if name: 
                update_kwargs['name'] = name
            if template_id:
                update_kwargs['default_template_id'] = template_id
            
            if update_kwargs:
                self.onto_repo.update_series(code, **update_kwargs)

        # 2. Create Version (Package)
        version = self.onto_repo.get_latest_version(code) + 1
        
        # Create record first to get ID
        db_package = self.onto_repo.create_package(
            series_code=code,
            version=version, 
            id=custom_id,
            template_id=final_template_id
        )
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
        self.onto_repo.set_active_version(package.series_code, package_id)
        
        # 触发本地事件 (同步触发，但由于业务简单，暂不使用异步)
        dispatcher.dispatch("ontology.activated", {
            "name": package.series.name,
            "code": package.series_code,
            "version": package.version,
            "package_id": package.id
        })
        
        return package

    def list_ontologies(self, skip: int = 0, limit: int = 100, name: str = None, code: str = None, all_versions: bool = False) -> schemas.PaginatedOntologyResponse:
        # If all_versions is True and code is provided, we list versions of a series.
        # Otherwise, we list Series (OntologySeries).
        # To maintain API compatibility, we need to map Series + ActiveVersion to OntologyPackageResponse structure
        # OR update the API/Frontend to understand Series.
        # Given "Refactoring" phase usually implies better API, let's try to adapt the response.
        
        if all_versions and code:
             packages, total = self.onto_repo.list_packages(series_code=code, skip=skip, limit=limit)
             results = []
             for pkg in packages:
                  res_item = schemas.OntologyPackageResponse.model_validate(pkg)
                  # Manual population from Series
                  if pkg.series:
                       res_item.name = pkg.series.name # Name comes from Series
                       res_item.code = pkg.series.code
                  if pkg.template:
                       res_item.template_name = pkg.template.name
                  self._enrich_package_security_info(res_item)
                  results.append(res_item)
             return {"items": results, "total": total}

        # List Series
        series_list, total = self.onto_repo.get_series_list(skip, limit, name)
        results = []
        for series in series_list:
            # Construct a "Package-like" response for the frontend list
            # Ideally frontend should consume Series, but let's map it for now or update Schema?
            # Creating a composite object: Series info + Active Version info
            
            # Find active version or latest version
            active_pkg = self.onto_repo.get_active_package_by_code(series.code)
            latest_version = self.onto_repo.get_latest_version(series.code)
            
            # Base data from Series
            res_item = schemas.OntologyPackageResponse(
                id=active_pkg.id if active_pkg else "no-active-version", # Frontend needs ID for key
                code=series.code,
                name=series.name,
                version=latest_version, # Show latest version number
                upload_time=series.updated_at, # Show series update time
                status="READY", # Aggregate status?
                is_active=bool(active_pkg),
                description=series.description
            )
            
            # If active package exists, use its ID for operations? 
            # Actually, creating a new version uses POST /ontologies/{code}/versions
            # Detailed view uses GET /ontologies/{id} (Version ID)
            # So the ID in the list should probably be the Active Version ID if exists, or Latest Version ID?
            # If NO version exists (shouldn't happen if created via API), what ID to return?
            
            target_pkg = active_pkg
            if not target_pkg:
                 # Try to get latest package to provide an ID for details view
                 target_pkg = self.onto_repo.get_latest_package_by_code(series.code)
            
            if target_pkg:
                res_item.id = target_pkg.id
                res_item.upload_time = target_pkg.upload_time
                res_item.status = target_pkg.status
                res_item.file_count = len(target_pkg.files)
                # Template info: Series Default or Version specific? 
                # List shows "Parsing Template". Should show what's effective?
                # Let's show Series Default if no active version, or Active Version's template.
                if target_pkg.template:
                     res_item.template_id = target_pkg.template_id
                     res_item.template_name = target_pkg.template.name
                elif series.default_template:
                     res_item.template_id = series.default_template_id
                     res_item.template_name = series.default_template.name
                
                self._enrich_package_security_info(res_item)
            else:
                 # Series with no versions (possible if cleanup or error)
                 res_item.id = "empty"
                 res_item.status = "EMPTY"

            results.append(res_item)
            
        return {"items": results, "total": total}

    def list_versions(self, code: str, skip: int = 0, limit: int = 100) -> schemas.PaginatedOntologyResponse:
        # Specialized method for versions of a specific ontology
        return self.list_ontologies(skip, limit, code=code, all_versions=True)

    def _enrich_package_security_info(self, pkg: schemas.OntologyPackageResponse):
        if pkg.is_active:
            pkg.is_deletable = False
            pkg.deletable_reason = "当前版本已启用"
        else:
             in_use_ids = self.webhook_service.get_in_use_package_ids(pkg.code)
             if pkg.id in in_use_ids:
                pkg.is_deletable = False
                pkg.deletable_reason = "该版本正在 Webhook 订阅中使用"
             else:
                pkg.is_deletable = True
                pkg.deletable_reason = None

    def get_ontology_detail(self, package_id: str):
        package = self.onto_repo.get_package(package_id)
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Convert to Pydantic model
        result = schemas.OntologyPackageDetailResponse.model_validate(package)
        
        # Populate Series Info
        if package.series:
            result.name = package.series.name
            result.code = package.series.code
            if not result.description:
                result.description = package.series.description

        # Populate template_name
        if package.template:
            result.template_name = package.template.name

        # 详情页同样补充安全性标记
        in_use_ids = self.webhook_service.get_in_use_package_ids(result.code) # Use Code
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
        in_use_ids = self.webhook_service.get_in_use_package_ids(package.series_code) # Use Code
        if package.id in in_use_ids:
            raise HTTPException(status_code=400, detail="该版本正在 Webhook 订阅中使用，不能删除")

        self.onto_repo.delete_package(package_id)
        storage_path = self._get_storage_path(package_id)
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)
            
        # Delete source zip file
        zip_path = self.get_source_zip_path(package_id)
        if os.path.exists(zip_path):
            os.remove(zip_path)

    def get_source_zip_path(self, package_id: str) -> str:
        # This belongs more to a StorageService but we'll put it here for now
        # Actually manager.py had a simple logic for this
        return os.path.join(BASE_STORAGE_DIR, f"{package_id}.zip") # Wait, manager.py just returned a path

    def list_relations(self, package_id: str, skip: int = 0, limit: int = 100) -> schemas.PaginatedOntologyRelationResponse:
        items, total = self.onto_repo.get_relations(package_id, skip, limit)
        return {"items": items, "total": total}

    async def compare_packages(self, base_id: str, target_id: str) -> schemas.OntologyComparisonResponse:
        """比较两个本体版本的差异 (Beyond Compare 风格)"""
        base_pkg = self.onto_repo.get_package(base_id)
        target_pkg = self.onto_repo.get_package(target_id)
        
        if not base_pkg or not target_pkg:
            raise HTTPException(status_code=404, detail="Package not found")

        base_files = {f.file_path: f for f in base_pkg.files}
        target_files = {f.file_path: f for f in target_pkg.files}

        all_paths = sorted(set(base_files.keys()) | set(target_files.keys()))
        diff_results = []

        for path in all_paths:
            status = "unchanged"
            base_content = None
            target_content = None

            # 识别文本文件后缀
            text_extensions = ('.md', '.txt', '.json', '.yaml', '.yml', '.ttl', '.owl', '.xml', '.csv', '.py', '.js', '.css')
            is_text = path.lower().endswith(text_extensions)

            if path in target_files and path not in base_files:
                status = "added"
                if is_text:
                    try:
                        with open(os.path.join(self._get_storage_path(target_id), path), 'r', encoding='utf-8') as f:
                            target_content = f.read()
                    except: pass
            elif path in base_files and path not in target_files:
                status = "deleted"
                if is_text:
                    try:
                        with open(os.path.join(self._get_storage_path(base_id), path), 'r', encoding='utf-8') as f:
                            base_content = f.read()
                    except: pass
            else:
                # 两个版本都存在，检查内容差异
                base_physical_path = os.path.join(self._get_storage_path(base_id), path)
                target_physical_path = os.path.join(self._get_storage_path(target_id), path)
                
                try:
                    if is_text:
                        with open(base_physical_path, 'r', encoding='utf-8') as f1, \
                             open(target_physical_path, 'r', encoding='utf-8') as f2:
                            c1 = f1.read()
                            c2 = f2.read()
                        
                        if c1 != c2:
                            status = "modified"
                            base_content = c1
                            target_content = c2
                    else:
                        # 简单检查文件大小，如果不同则标记为已修改
                        if os.path.getsize(base_physical_path) != os.path.getsize(target_physical_path):
                            status = "modified"
                except Exception as e:
                    logger.warning(f"Error comparing {path}: {e}")
                    status = "modified"

            diff_results.append(schemas.FileDiff(
                file_path=path,
                status=status,
                base_content=base_content,
                target_content=target_content
            ))

        return schemas.OntologyComparisonResponse(
            base_version=base_pkg.version,
            target_version=target_pkg.version,
            files=diff_results
        )
