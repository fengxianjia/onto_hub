import re
import yaml
import os
import logging
from typing import List, Tuple, Dict, Any
from .base import BaseParser
from ...models import OntologyFile

logger = logging.getLogger(__name__)

class MarkdownParser(BaseParser):
    @property
    def supported_extensions(self) -> List[str]:
        return ['.md', '.markdown']

    def parse(self, file_record: OntologyFile, content: str, rules: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        # 1. 解析 Frontmatter
        metadata, body = self._parse_frontmatter(content)
        
        # 2. 提取正则属性
        regex_attributes = self._extract_attributes(body, rules)
        
        # 3. 提取表格属性 (迁移逻辑)
        table_attributes = self._extract_table_attributes(body, rules)
        
        # 4. 合并
        final_metadata = {**metadata, **regex_attributes, **table_attributes}
        
        # 5. 提取 WikiLinks
        wiki_link_pattern = re.compile(r'\[\[(.*?)(?:\|.*?)?\]\]')
        links = wiki_link_pattern.findall(body)
        
        # 返回 body 供后续可能的全文索引或其他用途使用（虽然当前核心只存 metadata）
        # 这里为了保持一致性，我们将 body 放入 metadata 的一个特殊字段或直接处理
        # 按照现有逻辑，Service 需要 entity_name 和 category_name，这部分由 Service 统一处理
        # 插件只负责从内容中“抠”出结构化数据
        
        return final_metadata, links, body

    def _parse_frontmatter(self, content: str):
        if content.startswith("---\n"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_text = parts[1]
                body = parts[2]
                try:
                    metadata = yaml.safe_load(yaml_text)
                    if isinstance(metadata, dict):
                        return metadata, body
                except Exception:
                    pass
        return {}, content

    def _extract_attributes(self, content: str, rules: dict) -> dict:
        attributes = {}
        attr_rules = rules.get("attribute", {})
        
        # Regex Extraction
        regex_patterns = attr_rules.get("regex_patterns", [])
        for rule in regex_patterns:
            key = rule.get("key")
            pattern = rule.get("pattern")
            if not key or not pattern: continue
            try:
                compiled = re.compile(pattern, re.MULTILINE)
                match = compiled.search(content)
                if match:
                    attributes[key] = match.group(1).strip() if match.groups() else match.group(0).strip()
            except Exception:
                continue
        return attributes

    def _extract_table_attributes(self, content: str, rules: dict) -> dict:
        attributes = {}
        attr_rules = rules.get("attribute", {})
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
        lines = content.split('\n')
        table_start_index = -1
        for i, line in enumerate(lines):
            line = line.strip()
            if not line.startswith('|'): continue
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line.startswith('|') and '---' in next_line:
                    headers = [h.strip() for h in line.strip('|').split('|')]
                    if any(h in header_mapping for h in headers):
                        table_start_index = i
                        break
        
        if table_start_index == -1: return []
            
        header_line = lines[table_start_index].strip()
        raw_headers = [h.strip() for h in header_line.strip('|').split('|')]
        
        rows = []
        for i in range(table_start_index + 2, len(lines)):
            line = lines[i].strip()
            if not line.startswith('|'): break
            cells = [c.strip() for c in line.strip('|').split('|')]
            row_data = {}
            for col_idx, header in enumerate(raw_headers):
                if header in header_mapping:
                    key = header_mapping[header]
                    row_data[key] = cells[col_idx] if col_idx < len(cells) else ""
            if row_data: rows.append(row_data)
        return rows
