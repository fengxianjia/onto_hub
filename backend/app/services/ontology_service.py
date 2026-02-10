import os
import shutil
import zipfile
import logging
import json
import aiofiles
from datetime import datetime
from fastapi import UploadFile
from typing import List, Optional

from ..repositories.ontology_repo import OntologyRepository
from ..repositories.webhook_repo import WebhookRepository
from ..core.events import dispatcher
from .. import models, schemas, utils
from ..core.results import ServiceResult, ServiceStatus
from ..core.errors import BusinessCode
from ..config import settings

logger = logging.getLogger(__name__)

# OntologyService will use settings.STORAGE_DIR via dynamic property

class OntologyService:
    def __init__(self, onto_repo: OntologyRepository, webhook_repo: WebhookRepository, webhook_service: 'WebhookService' = None):
        self.onto_repo = onto_repo
        self.webhook_repo = webhook_repo
        self.webhook_service = webhook_service

    @property
    def storage_dir(self) -> str:
        """Dynamically get storage directory from settings."""
        path = settings.STORAGE_DIR
        os.makedirs(path, exist_ok=True)
        return path

    async def update_ontology_series(self, code: str, series_in: schemas.OntologySeriesUpdate) -> ServiceResult[models.OntologySeries]:
        series = self.onto_repo.get_series(code)
        if not series:
            return ServiceResult.failure_result(ServiceStatus.NOT_FOUND, f"Ontology '{code}' not found")
        
        updated = self.onto_repo.update_series(
            code, 
            name=series_in.name, 
            description=series_in.description, 
            default_template_id=series_in.default_template_id
        )
        return ServiceResult.success_result(updated)
    
    async def reparse_ontology_package(self, package_id: str, template_id: Optional[str] = None) -> ServiceResult[bool]:
        package = self.onto_repo.get_package(package_id)
        if not package:
            return ServiceResult.failure_result(ServiceStatus.NOT_FOUND, f"Package '{package_id}' not found")
        
        # If no template_id provided, use the one already on the package or series default
        final_template_id = template_id
        if not final_template_id:
            final_template_id = package.template_id
            if not final_template_id:
                series = self.onto_repo.get_series(package.series_code)
                final_template_id = series.default_template_id if series else None
        
        if not final_template_id:
            return ServiceResult.failure_result(ServiceStatus.FAILURE, "No parsing template associated with this ontology")
        
        # We don't background task here, we just return the template_id to use
        # The caller (main.py) will add it to background tasks
        return ServiceResult.success_result(final_template_id)

    def _get_storage_path(self, package_id: str) -> str:
        return os.path.join(self.storage_dir, package_id)

    def _decode_zip_path(self, raw_path: str) -> str:
        """
        解决 Linux 环境下 ZIP 压缩包内中文文件名乱码问题。
        zipfile 模块默认对于非 UTF-8 标记的文件名使用 cp437 编码，
        而 Windows 下创建的压缩包通常使用 GBK。
        """
        try:
            # 尝试先转换回字节流，再用 GBK 解码
            return raw_path.encode('cp437').decode('gbk')
        except (UnicodeEncodeError, UnicodeDecodeError):
            # 如果转换失败（说明本身就是 UTF-8 或者其他情况），则返回原值
            return raw_path

    def _safe_extract(self, zip_ref: zipfile.ZipFile, extract_path: str):
        """
        带安全校验的解压逻辑：
        1. 防御 Zip Slip (路径遍历)
        2. 防御 ZIP 炸弹 (限制总大小和文件数量)
        """
        MAX_FILE_COUNT = 1000
        MAX_TOTAL_SIZE = 500 * 1024 * 1024  # 500MB
        
        total_size = 0
        file_count = 0
        
        # 预检查文件数量
        infolist = zip_ref.infolist()
        if len(infolist) > MAX_FILE_COUNT:
            raise ValueError(f"压缩包内文件数量过多 (上限 {MAX_FILE_COUNT})")

        for member in infolist:
            # 修正路径编码并防御 Zip Slip
            decoded_member = self._decode_zip_path(member.filename)
            
            # 使用 os.path.abspath 进行归一化路径校验
            target_path = os.path.abspath(os.path.join(extract_path, decoded_member))
            if not target_path.startswith(os.path.abspath(extract_path)):
                logger.warning(f"检测到潜在的路径遍历攻击 (Zip Slip): {member.filename}")
                continue
            
            # 过滤目录项，只处理文件
            if member.is_dir():
                os.makedirs(target_path, exist_ok=True)
                continue

            # 统计总大小并防御 ZIP 炸弹
            total_size += member.file_size
            if total_size > MAX_TOTAL_SIZE:
                raise ValueError(f"解压后总大小超过限制 (上限 {MAX_TOTAL_SIZE // (1024*1024)}MB)")
            
            file_count += 1
            
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with zip_ref.open(member) as source, open(target_path, "wb") as target:
                # 分块读取，并在写入过程中实时检查总大小
                # member.file_size 可能被恶意修改，所以必须检查实际解压后写入的大小
                CHUNK_SIZE = 1024 * 1024 # 1MB
                while True:
                    chunk = source.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    target.write(chunk)
                    total_size += len(chunk)
                    
                    if total_size > MAX_TOTAL_SIZE:
                        # 清理已解压的文件
                        logger.error(f"解压后总大小超过限制 ({MAX_TOTAL_SIZE} 字节)，操作中止")
                        raise ValueError(f"解压后总大小超过限制 (上限 {MAX_TOTAL_SIZE // (1024*1024)}MB)")

    async def create_ontology(self, file: UploadFile, code: str, custom_id: str = None, name: str = None, template_id: str = None, is_initial: bool = False) -> ServiceResult[models.OntologyPackage]:
        # 严格分层：校验逻辑下沉
        if is_initial:
            existing_version = self.onto_repo.get_latest_version(code)
            if existing_version > 0:
                return ServiceResult.failure_result(
                    ServiceStatus.ALREADY_EXISTS, 
                    f"Ontology code '{code}' already exists.",
                    business_code=BusinessCode.ONTOLOGY_ALREADY_EXISTS
                )
            
            if name:
                existing_name_series = self.onto_repo.get_series_by_name(name)
                if existing_name_series:
                    return ServiceResult.failure_result(
                        ServiceStatus.DUPLICATE_NAME, 
                        f"Ontology name '{name}' already exists.",
                        business_code=BusinessCode.ONTOLOGY_NAME_ALREADY_EXISTS
                    )
        else:
            existing_version = self.onto_repo.get_latest_version(code)
            if existing_version == 0:
                return ServiceResult.failure_result(
                    ServiceStatus.NOT_FOUND, 
                    f"Ontology code '{code}' not found.",
                    business_code=BusinessCode.ONTOLOGY_NOT_FOUND
                )

        # 保存文件并创建记录
        temp_zip = os.path.join(self.storage_dir, f"temp_{datetime.now().timestamp()}.zip")
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
            
            return ServiceResult.success_result(db_package)
        finally:
            if os.path.exists(temp_zip):
                os.remove(temp_zip)

    def activate_ontology(self, package_id: str) -> ServiceResult[models.OntologyPackage]:
        package = self.onto_repo.get_package(package_id)
        if not package:
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND, 
                "Package not found",
                business_code=BusinessCode.ONTOLOGY_NOT_FOUND
            )
        
        # 激活前先确保此本体包的基础信息已同步
        self.onto_repo.set_active_version(package.series_code, package_id)
        
        # 触发本地事件 (同步触发，但由于业务简单，暂不使用异步)
        dispatcher.dispatch("ontology.activated", {
            "name": package.series.name,
            "code": package.series_code,
            "version": package.version,
            "package_id": package.id
        })
        
        return ServiceResult.success_result(package)

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

    def get_ontology_detail(self, package_id: str) -> ServiceResult[schemas.OntologyPackageDetailResponse]:
        package = self.onto_repo.get_package(package_id)
        if not package:
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND, 
                "Package not found",
                business_code=BusinessCode.ONTOLOGY_NOT_FOUND
            )
        
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

        return ServiceResult.success_result(result)

    def get_file_content(self, package_id: str, relative_path: str) -> ServiceResult[str]:
        # Check storage
        file_path = os.path.join(self._get_storage_path(package_id), relative_path)
        if not os.path.exists(file_path):
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND, 
                "File not found on disk",
                business_code=BusinessCode.RESOURCE_NOT_FOUND
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ServiceResult.success_result(f.read())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

    def delete_version(self, package_id: str) -> ServiceResult[None]:
        """删除指定版本的本体及物理文件"""
        package = self.onto_repo.get_package(package_id)
        if not package:
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND, 
                "Package not found",
                business_code=BusinessCode.ONTOLOGY_NOT_FOUND
            )
            
        # 安全校验：Active 的不能删
        if package.is_active:
            return ServiceResult.failure_result(ServiceStatus.VERSION_ACTIVE, "正在启用的版本不能删除")
            
        # 安全校验：订阅者正在使用的不能删
        in_use_ids = self.webhook_service.get_in_use_package_ids(package.series_code)
        if package.id in in_use_ids:
            return ServiceResult.failure_result(ServiceStatus.RESOURCE_IN_USE, "该版本正在 Webhook 订阅中使用，不能删除")

        self.onto_repo.delete_package(package_id)
        storage_path = self._get_storage_path(package_id)
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)
            
        # Delete source zip file
        zip_path = self.get_source_zip_path(package_id)
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        return ServiceResult.success_result()

    def delete_ontology_series(self, code: str) -> ServiceResult[None]:
        """删除整个本体系列及其所有物理文件 (高危操作)"""
        series = self.onto_repo.get_series(code)
        if not series:
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND, 
                "Ontology series not found",
                business_code=BusinessCode.ONTOLOGY_NOT_FOUND
            )

        # 1. 物理清理：删除该系列下所有版本的物理文件
        packages, _ = self.onto_repo.list_packages(series_code=code, limit=1000)
        for pkg in packages:
            storage_path = self._get_storage_path(pkg.id)
            if os.path.exists(storage_path):
                shutil.rmtree(storage_path)
            
            zip_path = self.get_source_zip_path(pkg.id)
            if os.path.exists(zip_path):
                os.remove(zip_path)
        
        # 2. 数据库清理：利用 Repository 执行级联删除
        self.onto_repo.delete_series(code)
        logger.info(f"Ontology series '{code}' and its {len(packages)} versions have been deleted.")
        return ServiceResult.success_result()

    def delete_ontology(self, package_id: str):
        # Backward compatibility alias
        return self.delete_version(package_id)

    def get_source_zip_path(self, package_id: str) -> str:
        # This belongs more to a StorageService but we'll put it here for now
        # Actually manager.py had a simple logic for this
        return os.path.join(self.storage_dir, f"{package_id}.zip") # Wait, manager.py just returned a path

    def list_relations(self, package_id: str, skip: int = 0, limit: int = 100) -> schemas.PaginatedOntologyRelationResponse:
        items, total = self.onto_repo.get_relations(package_id, skip, limit)
        return {"items": items, "total": total}

    async def compare_packages(self, base_id: str, target_id: str) -> ServiceResult[schemas.OntologyComparisonResponse]:
        """比较两个本体版本的差异 (Beyond Compare 风格)"""
        base_pkg = self.onto_repo.get_package(base_id)
        target_pkg = self.onto_repo.get_package(target_id)
        
        if not base_pkg or not target_pkg:
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND, 
                "Package not found",
                business_code=BusinessCode.ONTOLOGY_NOT_FOUND
            )

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

        return ServiceResult.success_result(schemas.OntologyComparisonResponse(
            base_version=base_pkg.version,
            target_version=target_pkg.version,
            files=diff_results
        ))

    def get_version_package_path(self, code: str, version: int) -> ServiceResult[str]:
        """获取指定版本的原始本体 ZIP 包物理路径"""
        package = self.onto_repo.get_package_by_version(code, version)
        if not package:
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND,
                f"Version {version} of ontology {code} not found",
                business_code=BusinessCode.ONTOLOGY_NOT_FOUND
            )
            
        zip_path = self.get_source_zip_path(package.id)
        if not os.path.exists(zip_path):
            return ServiceResult.failure_result(
                ServiceStatus.NOT_FOUND,
                "Source ZIP file not found on storage",
                business_code=BusinessCode.FILE_NOT_FOUND
            )
            
        return ServiceResult.success_result(zip_path)
