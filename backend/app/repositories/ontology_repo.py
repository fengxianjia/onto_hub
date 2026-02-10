from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
from typing import List, Optional, Tuple
from .. import models, schemas

class OntologyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_series(self, code: str) -> Optional[models.OntologySeries]:
        return self.db.query(models.OntologySeries).filter(models.OntologySeries.code == code).first()

    def get_series_by_name(self, name: str) -> Optional[models.OntologySeries]:
        return self.db.query(models.OntologySeries).filter(models.OntologySeries.name == name).first()

    def get_series_list(self, skip: int = 0, limit: int = 100, name: str = None) -> Tuple[List[models.OntologySeries], int]:
        query = self.db.query(models.OntologySeries)
        if name:
            query = query.filter(models.OntologySeries.name.contains(name))
        
        total = query.count()
        items = query.order_by(models.OntologySeries.updated_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def create_series(self, code: str, name: str, description: str = None, default_template_id: str = None) -> models.OntologySeries:
        db_series = models.OntologySeries(
            code=code,
            name=name,
            description=description,
            default_template_id=default_template_id
        )
        self.db.add(db_series)
        self.db.commit()
        self.db.refresh(db_series)
        return db_series
        
    def update_series(self, code: str, name: str = None, description: str = None, default_template_id: str = None):
        series = self.get_series(code)
        if not series:
            return
        
        if name:
            series.name = name
        if description is not None:
             series.description = description
        if default_template_id is not None:
             series.default_template_id = default_template_id
        
        self.db.commit()
        self.db.refresh(series)
        return series

    def create_package(self, series_code: str, version: int, id: str = None, template_id: str = None) -> models.OntologyPackage:
        db_package = models.OntologyPackage(
            id=id, # Allow custom ID
            series_code=series_code,
            version=version,
            status="READY",
            template_id=template_id
        )
        self.db.add(db_package)
        self.db.commit()
        self.db.refresh(db_package)
        return db_package

    def get_package(self, package_id: str) -> Optional[models.OntologyPackage]:
        return self.db.query(models.OntologyPackage).filter(models.OntologyPackage.id == package_id).first()

    def get_active_package_by_code(self, code: str) -> Optional[models.OntologyPackage]:
        # Active package for a series code
        return self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.series_code == code,
            models.OntologyPackage.is_active == True
        ).first()

    def get_latest_package_by_code(self, code: str) -> Optional[models.OntologyPackage]:
        """获取特定系列下版本号最高的一个包"""
        return self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.series_code == code
        ).order_by(models.OntologyPackage.version.desc()).first()

    def get_latest_version(self, code: str) -> int:
        # Use series_code to find the latest version
        latest = self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.series_code == code
        ).order_by(models.OntologyPackage.version.desc()).first()
        return latest.version if latest else 0

    def list_packages(self, series_code: str, skip: int = 0, limit: int = 100) -> Tuple[List[models.OntologyPackage], int]:
        # List versions for a series
        query = self.db.query(models.OntologyPackage).filter(models.OntologyPackage.series_code == series_code)
        total = query.count()
        items = query.order_by(models.OntologyPackage.version.desc()).offset(skip).limit(limit).all()
        return items, total

    def delete_package(self, package_id: str):
        package = self.get_package(package_id)
        if package:
            self.db.delete(package)
            self.db.commit()

    def delete_series(self, code: str):
        """删除整个本体系列及其下所有内容 (级联)"""
        series = self.get_series(code)
        if series:
            self.db.delete(series)
            self.db.commit()

    def set_active_version(self, series_code: str, package_id: str):
        # 1. 停用该 Series 下的所有历史版本
        self.db.query(models.OntologyPackage).filter(
            models.OntologyPackage.series_code == series_code
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

    def get_relations(self, package_id: str, skip: int = 0, limit: int = 100) -> Tuple[List[models.OntologyRelation], int]:
        query = self.db.query(models.OntologyRelation).filter(models.OntologyRelation.package_id == package_id)
        # Eager load source and target entities
        query = query.options(joinedload(models.OntologyRelation.source), joinedload(models.OntologyRelation.target))
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
