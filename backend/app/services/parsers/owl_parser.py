import logging
import os
from typing import List, Tuple, Dict, Any
from rdflib import Graph, RDF, RDFS, OWL, URIRef
from .base import BaseParser
from ...models import OntologyFile

logger = logging.getLogger(__name__)

class OWLParser(BaseParser):
    @property
    def supported_extensions(self) -> List[str]:
        return ['.owl', '.rdf', '.ttl', '.n3']

    def parse(self, file_record: OntologyFile, content: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析 OWL/RDF 本体文件，提取所有类作为独立实体
        """
        g = Graph()
        ext = os.path.splitext(file_record.file_path)[1].lower()
        format_map = {
            '.owl': 'xml',
            '.rdf': 'xml',
            '.ttl': 'turtle',
            '.n3': 'n3'
        }
        
        try:
            g.parse(data=content, format=format_map.get(ext, 'xml'))
        except Exception as e:
            logger.error(f"Failed to parse RDF content: {e}")
            return []

        # 1. 预提取所有类的关系 (subClassOf)
        # 用字典存储关系，方便后续组装
        class_links = {}
        for s, o in g.subject_objects(RDFS.subClassOf):
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                if s not in class_links: class_links[s] = []
                target_name = self._get_label_or_fragment(g, o)
                class_links[s].append(target_name)

        # 2. 遍历所有类并构造实体列表
        entities = []
        for s in g.subjects(RDF.type, OWL.Class):
            if not isinstance(s, URIRef): continue
            
            name = self._get_label_or_fragment(g, s)
            metadata = {
                "uri": str(s),
                "type": "Class",
                "label": str(g.value(s, RDFS.label)) if g.value(s, RDFS.label) else "",
                "comment": str(g.value(s, RDFS.comment)) if g.value(s, RDFS.comment) else ""
            }
            
            entities.append({
                "name": name,
                "metadata": metadata,
                "links": class_links.get(s, []),
                "category": "OWL Class" # 可选，Service 逻辑会处理
            })

        return entities

    def _get_label_or_fragment(self, g, uri):
        label = g.value(uri, RDFS.label)
        if label:
            return str(label)
        # fallback to fragment
        if "#" in uri:
            return uri.split("#")[-1]
        return uri.split("/")[-1]
