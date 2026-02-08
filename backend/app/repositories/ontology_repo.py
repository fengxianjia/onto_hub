from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional, Tuple
from .. import models, schemas

class OntologyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_package(self, name: str, version: int, code: str = None, description: str = None, id: str = None) -> models.OntologyPackage:
        db_package = models.OntologyPackage(
            id=id, # Allow custom ID
            name=name,
            code=code,
            version=version,
            description=description,
            status="READY"
        )
        self.db.add(db_package)
        self.db.commit()
        self.db.refresh(db_package)
        return db_package

    def get_package(self, package_id: str) -> Optional[models.OntologyPackage]:
        return self.db.query(models.OntologyPackage).filter(models.OntologyPackage.id == package_id).first()

    def get_active_package_by_name(self, name: str) -> Optional[models.OntologyPackage]:
        return self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.name == name,
            models.OntologyPackage.is_active == True
        ).first()

    def get_latest_version(self, code: str) -> int:
        # Use code to find the latest version
        latest = self.get_latest_package_by_code(code)
        return latest.version if latest else 0

    def get_latest_package_by_code(self, code: str) -> Optional[models.OntologyPackage]:
        return self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.code == code
        ).order_by(models.OntologyPackage.version.desc()).first()

    def list_packages(self, skip: int = 0, limit: int = 100, name: str = None, code: str = None, all_versions: bool = False) -> Tuple[List[models.OntologyPackage], int]:
        query = self.db.query(models.OntologyPackage)
        if name:
            query = query.filter(models.OntologyPackage.name.contains(name)) # Fuzzy search for name
        if code:
            query = query.filter(models.OntologyPackage.code == code)
        
        if not all_versions:
            # Only active versions or the most recent ones if no active exists? 
            # Current logic: show active only OR specified version.
            # Let's stick to the current logic in manager.py
            query = query.filter(models.OntologyPackage.is_active == True)
            
        total = query.count()
        items = query.order_by(models.OntologyPackage.upload_time.desc()).offset(skip).limit(limit).all()
        return items, total

    def delete_package(self, package_id: str):
        package = self.get_package(package_id)
        if package:
            self.db.delete(package)
            self.db.commit()

    def set_active_version(self, code: str, package_id: str):
        # 1. 停用该 Code 下的所有历史版本
        self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.code == code
        ).update({"is_active": False}, synchronize_session="fetch")
        
        # 2. 激活指定版本
        self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.id == package_id
        ).update({"is_active": True}, synchronize_session="fetch")
        
        self.db.commit()

    def create_file(self, package_id: str, file_path: str, file_size: int, content_preview: str = None) -> models.OntologyFile:
        db_file = models.OntologyFile(
            package_id=package_id,
            file_path=file_path,
            file_size=file_size,
            content_preview=content_preview
        )
        self.db.add(db_file)
        self.db.commit()
        return db_file

    def get_file(self, package_id: str, relative_path: str) -> Optional[models.OntologyFile]:
        return self.db.query(models.OntologyFile).filter(
            models.OntologyFile.package_id == package_id,
            models.OntologyFile.file_path == relative_path
        ).first()

    def get_package_files(self, package_id: str) -> List[models.OntologyFile]:
        return self.db.query(models.OntologyFile).filter(models.OntologyFile.package_id == package_id).all()

    def create_files_batch(self, file_data_list: List[dict]):
        """批量创建文件记录以减少 commit 次数"""
        if not file_data_list:
            return
        
        objects = [models.OntologyFile(**data) for data in file_data_list]
        self.db.bulk_save_objects(objects)
        self.db.commit()
