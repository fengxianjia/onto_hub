import os
import sys
import json
import pytest
from unittest.mock import patch

# 注入项目根目录到 PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.parsing_service import ParsingService
from app.models import OntologyPackage, OntologyFile, ParsingTemplate
from app import models

TTL_CONTENT = """
@prefix : <http://example.org/onto#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:Animal a owl:Class ;
    rdfs:label "Animal" .

:Dog a owl:Class ;
    rdfs:label "Dog" ;
    rdfs:subClassOf :Animal .
"""

@pytest.mark.asyncio
async def test_owl_parsing_logic(test_db_session, tmp_path):
    # 1. 准备测试环境
    pkg_id = models.generate_uuid()
    package = OntologyPackage(id=pkg_id, series_code="owl-test", version=1)
    test_db_session.add(package)
    
    # 创建临时 TTL 文件
    pkg_dir = tmp_path / pkg_id
    pkg_dir.mkdir()
    owl_file_path = pkg_dir / "test.ttl"
    owl_file_path.write_text(TTL_CONTENT, encoding='utf-8')
    
    file_record = OntologyFile(
        package_id=pkg_id,
        file_path="test.ttl",
        file_size=len(TTL_CONTENT)
    )
    test_db_session.add(file_record)
    
    # 规则设定：从 metadata 取名称
    template = ParsingTemplate(
        id=models.generate_uuid(),
        name="OWL Template",
        rules=json.dumps({
            "entity": {
                "name_source": "metadata:name",
                "category_source": "directory"
            }
        })
    )
    test_db_session.add(template)
    test_db_session.commit()
    
    # 2. 执行解析
    service = ParsingService(test_db_session)
    # 修正：通过 patch 动态重定向 storage_dir
    from unittest.mock import PropertyMock
    with patch("app.services.parsing_service.ParsingService.storage_dir", new_callable=PropertyMock) as mock_storage:
        mock_storage.return_value = str(tmp_path)
        service.parse_package(pkg_id, template.id)
    
    # 3. 验证结果
    entities = test_db_session.query(models.OntologyEntity).filter_by(package_id=pkg_id).all()
    # 验证是否解析出了 2 个实体 (Animal, Dog)
    assert len(entities) == 2
    
    entity_names = [e.name for e in entities]
    assert "Animal" in entity_names
    assert "Dog" in entity_names
    
    # 验证关系是否建立 (Dog -> Animal)
    relations = test_db_session.query(models.OntologyRelation).filter_by(package_id=pkg_id).all()
    assert len(relations) == 1
    
    # 获取实体对象进行详细校验
    dog_entity = next(e for e in entities if e.name == "Dog")
    animal_entity = next(e for e in entities if e.name == "Animal")
    
    relation = relations[0]
    assert relation.source_id == dog_entity.id
    assert relation.target_id == animal_entity.id
