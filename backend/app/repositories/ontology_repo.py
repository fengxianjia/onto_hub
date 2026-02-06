from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional, Tuple
from .. import models, schemas

class OntologyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_package(self, name: str, version: int, description: str = None) -> models.OntologyPackage:
        db_package = models.OntologyPackage(
            name=name,
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

    def get_latest_version(self, name: str) -> int:
        latest = self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.name == name
        ).order_by(models.OntologyPackage.version.desc()).first()
        return latest.version if latest else 0

    def list_packages(self, skip: int = 0, limit: int = 100, name: str = None, all_versions: bool = False) -> List[models.OntologyPackage]:
        query = self.db.query(models.OntologyPackage)
        if name:
            query = query.filter(models.OntologyPackage.name == name)
        
        if not all_versions:
            # Only active versions or the most recent ones if no active exists? 
            # Current logic: show active only OR specified version.
            # Let's stick to the current logic in manager.py
            query = query.filter(models.OntologyPackage.is_active == True)
            
        return query.order_by(models.OntologyPackage.upload_time.desc()).offset(skip).limit(limit).all()

    def delete_package(self, package_id: str):
        package = self.get_package(package_id)
        if package:
            self.db.delete(package)
            self.db.commit()

    def set_active_version(self, name: str, package_id: str):
        # 1. 停用该名称下的所有历史版本
        self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.name == name
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
