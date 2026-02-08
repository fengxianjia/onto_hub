import re
import yaml
import os
import json
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from .. import models, schemas
from ..models import OntologyPackage, OntologyFile, ParsingTemplate, OntologyEntity, OntologyRelation

logger = logging.getLogger(__name__)

class ParsingService:
    def __init__(self, db: Session):
        self.db = db

    def _extract_attributes(self, content: str, rules: dict) -> dict:
        attributes = {}
        attr_rules = rules.get("attribute", {})
        
        # 1. Regex Extraction
        regex_patterns = attr_rules.get("regex_patterns", [])
        for rule in regex_patterns:
            key = rule.get("key")
            pattern = rule.get("pattern")
            if not key or not pattern:
                continue
            try:
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    if match.groups():
                        attributes[key] = match.group(1).strip()
                    else:
                        attributes[key] = match.group(0).strip()
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
        
        # 2. Table Row Extraction
        strategies = attr_rules.get("strategies", [])
        for strategy in strategies:
            if strategy.get("type") == "table_row":
                target_key = strategy.get("target_key", "properties")
                header_mapping = strategy.get("header_mapping", {})
                
                rows = self._parse_markdown_table(content, header_mapping)
                if rows:
                    attributes[target_key] = rows
                    
        return attributes

    def _parse_markdown_table(self, content: str, header_mapping: dict) -> List[dict]:
        """
        Parses the first table in the content that matches the header mapping.
        """
        lines = content.split('\n')
        table_start_index = -1
        
        # Find table header
        # Header must be followed by a separator line like |---|---|
        for i, line in enumerate(lines):
            line = line.strip()
            if not line.startswith('|'): continue
            
            # Potential header
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                # Check for separator line
                if next_line.startswith('|') and '---' in next_line:
                    # Found a table structure. Now check if headers match our mapping.
                    headers = [h.strip() for h in line.strip('|').split('|')]
                    
                    # Check if ANY of the mapped headers exist in this table
                    # Using set intersection to see if this table is relevant
                    mapped_headers_present = [h for h in headers if h in header_mapping]
                    
                    if mapped_headers_present:
                        table_start_index = i
                        break
        
        if table_start_index == -1:
            return []
            
        # Parse Headers
        header_line = lines[table_start_index].strip()
        raw_headers = [h.strip() for h in header_line.strip('|').split('|')]
        
        # Parse Rows
        rows = []
        for i in range(table_start_index + 2, len(lines)):
            line = lines[i].strip()
            if not line.startswith('|'):
                break # End of table
            
            cells = [c.strip() for c in line.strip('|').split('|')]
            
            # Handle row normalization (sometimes cells might be fewer than headers)
            row_data = {}
            for col_idx, header in enumerate(raw_headers):
                if header in header_mapping:
                    key = header_mapping[header]
                    val = cells[col_idx] if col_idx < len(cells) else ""
                    row_data[key] = val
            
            if row_data:
                rows.append(row_data)
                
        return rows

    def parse_package(self, package_id: str, template_id: str):
        logger.info(f"Starting parsing for package {package_id} with template {template_id}")
        
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
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "ontohub_storage", package_id)

        files = self.db.query(OntologyFile).filter(OntologyFile.package_id == package_id).all()
        
        entities_to_add = []
        relations_to_add = []
        parsed_files = [] 
        
        for file_record in files:
            full_path = os.path.join(base_dir, file_record.file_path)
            if not os.path.exists(full_path):
                logger.warning(f"File not found: {full_path}")
                continue
                
            if not full_path.endswith(".md"):
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            frontmatter, body = self._parse_frontmatter(content)
            
            # Extract Attributes
            regex_attributes = self._extract_attributes(body, rules)
            merged_metadata = {**frontmatter, **regex_attributes}
            
            entity_name = self._extract_entity_name(file_record, frontmatter, entity_rules)
            entity_category = self._extract_category(file_record, frontmatter, entity_rules)
            
            entity = OntologyEntity(
                package_id=package_id,
                name=entity_name,
                category=entity_category,
                metadata_json=json.dumps(merged_metadata, ensure_ascii=False),
                file_path=file_record.file_path
            )
            entity.id = models.generate_uuid()
            
            entities_to_add.append(entity)
            name_to_id_map[entity_name] = entity.id
            
            parsed_files.append({
                "entity_id": entity.id,
                "body": body,
                "frontmatter": frontmatter
            })

        self.db.add_all(entities_to_add)
        self.db.flush()
        
        wiki_link_pattern = re.compile(r'\[\[(.*?)(?:\|.*?)?\]\]')
        
        for pfile in parsed_files:
            source_id = pfile["entity_id"]
            body = pfile["body"]
            
            matches = wiki_link_pattern.findall(body)
            for target_name in matches:
                target_name = target_name.strip()
                if target_name in name_to_id_map:
                    target_id = name_to_id_map[target_name]
                    
                    if source_id == target_id:
                        continue
                        
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

    def _parse_frontmatter(self, content: str):
        """
        Simple YAML frontmatter parser.
        """
        if content.startswith("---\n"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_text = parts[1]
                body = parts[2]
                try:
                    metadata = yaml.safe_load(yaml_text)
                    if isinstance(metadata, dict):
                        return metadata, body
                except yaml.YAMLError:
                    pass
        return {}, content

    def _extract_entity_name(self, file_record: OntologyFile, frontmatter: dict, rules: dict) -> str:
        strategy = rules.get("name_source", "filename_no_ext")
        if strategy == "frontmatter:title":
            return frontmatter.get("title", os.path.splitext(os.path.basename(file_record.file_path))[0])
        else:
            # Default: filename without extension
            base = os.path.basename(file_record.file_path)
            return os.path.splitext(base)[0]

    def _extract_category(self, file_record: OntologyFile, frontmatter: dict, rules: dict) -> str:
        strategy = rules.get("category_source", "directory")
        if strategy == "frontmatter:type":
            return frontmatter.get("type", "Uncategorized")
        elif strategy == "directory":
            # Use parent directory name
            dirname = os.path.dirname(file_record.file_path)
            if not dirname or dirname == ".":
                return "Root"
            return os.path.basename(dirname)
        return "Uncategorized"
