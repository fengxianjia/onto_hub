import re
import yaml
import os
import json
import logging
import importlib
import pkgutil
from typing import List, Dict, Optional, Type
from sqlalchemy.orm import Session
from .. import models, schemas
from ..models import OntologyPackage, OntologyFile, ParsingTemplate, OntologyEntity, OntologyRelation
from .parsers.base import BaseParser

logger = logging.getLogger(__name__)

class ParsingService:
    def __init__(self, db: Session):
        self.db = db
        self._parsers: Dict[str, BaseParser] = {}
        self._register_parsers()

    @property
    def storage_dir(self) -> str:
        """Dynamically get storage directory from settings."""
        from ..config import settings
        return settings.STORAGE_DIR

    def _register_parsers(self):
        """
        自动发现并注册 app/services/parsers 目录下的解析器插件
        """
        try:
            import app.services.parsers as pars_pkg
            pkg_path = os.path.dirname(pars_pkg.__file__)
            
            for _, name, _ in pkgutil.iter_modules([pkg_path]):
                if name == 'base': continue
                
                try:
                    module_name = f"app.services.parsers.{name}"
                    module = importlib.import_module(module_name)
                    
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseParser) and 
                            attr is not BaseParser):
                            
                            parser_instance = attr()
                            for ext in parser_instance.supported_extensions:
                                self._parsers[ext.lower()] = parser_instance
                                logger.info(f"Registered parser {attr.__name__} for extension {ext}")
                except Exception as e:
                    logger.error(f"Failed to load parser plugin {name}: {e}")
        except Exception as e:
            logger.error(f"ParsingService initialization failed: {e}")

    def parse_package(self, package_id: str, template_id: str):
        logger.info(f"Starting plugin-based parsing for package {package_id} with template {template_id}")
        
        package = self.db.query(OntologyPackage).filter(OntologyPackage.id == package_id).first()
        template = self.db.query(ParsingTemplate).filter(ParsingTemplate.id == template_id).first()
        
        if not package or not template:
            logger.error("Package or Template not found")
            return
            
        self._clear_existing_data(package_id)
        
        try:
            rules = json.loads(template.rules)
        except json.JSONDecodeError:
            logger.error("Invalid JSON rules in template")
            return

        entity_rules = rules.get("entity", {})
        name_to_id_map = {} 
        base_dir = os.path.join(self.storage_dir, package_id)
        files = self.db.query(OntologyFile).filter(OntologyFile.package_id == package_id).all()
        
        entities_to_add = []
        relations_to_add = []
        parsed_results = [] 

        for file_record in files:
            full_path = os.path.join(base_dir, file_record.file_path)
            if not os.path.exists(full_path):
                logger.warning(f"File not found: {full_path}")
                continue
            
            ext = os.path.splitext(file_record.file_path)[1].lower()
            parser = self._parsers.get(ext)
            
            if not parser:
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                
                # 插件现在返回实体记录列表 [{'metadata': ..., 'links': ..., 'name': ...}, ...]
                parsed_entities = parser.parse(file_record, content, rules)
                
                for record in parsed_entities:
                    metadata = record.get("metadata", {})
                    links = record.get("links", [])
                    
                    # 确定实体名称：插件显式指定优先，否则用核心规则提取
                    entity_name = record.get("name") or self._extract_entity_name(file_record, metadata, entity_rules)
                    entity_category = record.get("category") or self._extract_category(file_record, metadata, entity_rules)
                    
                    entity = OntologyEntity(
                        package_id=package_id,
                        name=entity_name,
                        category=entity_category,
                        metadata_json=json.dumps(metadata, ensure_ascii=False),
                        file_path=file_record.file_path
                    )
                    entity.id = models.generate_uuid()
                    
                    entities_to_add.append(entity)
                    name_to_id_map[entity_name] = entity.id
                    
                    parsed_results.append({
                        "entity_id": entity.id,
                        "links": links
                    })
            except Exception as e:
                logger.error(f"Error parsing file {file_record.file_path} with {parser.__class__.__name__}: {e}")

        # 批量写入实体
        self.db.add_all(entities_to_add)
        self.db.flush()
        
        # 统一处理关系构建
        for result in parsed_results:
            source_id = result["entity_id"]
            for target_name in result["links"]:
                target_name = target_name.strip()
                if target_name in name_to_id_map:
                    target_id = name_to_id_map[target_name]
                    if source_id == target_id: continue
                        
                    rel = OntologyRelation(
                        package_id=package_id,
                        source_id=source_id,
                        target_id=target_id,
                        relation_type="related_to"
                    )
                    relations_to_add.append(rel)

        self.db.add_all(relations_to_add)
        
        try:
            self.db.commit()
            logger.info(f"Successfully parsed {len(entities_to_add)} entities and {len(relations_to_add)} relations.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit parsed data: {e}")
            raise

    def _clear_existing_data(self, package_id: str):
        self.db.query(OntologyRelation).filter(OntologyRelation.package_id == package_id).delete()
        self.db.query(OntologyEntity).filter(OntologyEntity.package_id == package_id).delete()
        self.db.commit()

    def _extract_entity_name(self, file_record: OntologyFile, metadata: dict, rules: dict) -> str:
        strategy = rules.get("name_source", "filename_no_ext")
        if strategy == "frontmatter:title" or strategy == "metadata:title":
            return metadata.get("title", os.path.splitext(os.path.basename(file_record.file_path))[0])
        else:
            base = os.path.basename(file_record.file_path)
            return os.path.splitext(base)[0]

    def _extract_category(self, file_record: OntologyFile, metadata: dict, rules: dict) -> str:
        strategy = rules.get("category_source", "directory")
        if strategy == "frontmatter:type" or strategy == "metadata:type":
            return metadata.get("type", "Uncategorized")
        elif strategy == "directory":
            dirname = os.path.dirname(file_record.file_path)
            if not dirname or dirname == ".":
                return "Root"
            return os.path.basename(dirname)
        return "Uncategorized"
