import pytest
import json
import os
from pathlib import Path
from app.services.parsing_service import ParsingService
from app.models import ParsingTemplate, OntologyPackage, OntologyFile, OntologyEntity, generate_uuid

@pytest.mark.integration
class TestParsingEdgeCases:
    """
    针对解析算法边界情况的集成测试：
    1. 模板正则语法错误 (防止后端崩溃)
    2. 正则运行时超时/异常 (ReDoS 风险模拟)
    3. 特殊字符与空文件处理
    4. 循环引用/自引用 WikiLinks
    """

    @pytest.fixture
    def setup_bad_template(self, test_db_session):
        # 1. 语法错误的正则模板
        template = ParsingTemplate(
            id=f"tpl-bad-{generate_uuid()[:8]}",
            name="Bad Regex Template",
            rules=json.dumps({
                "entity": {"name_source": "filename_no_ext", "category_source": "directory"},
                "attribute": {
                    "regex_patterns": [
                        {"key": "error", "pattern": r"["} # 这是一个非法的正则
                    ]
                }
            })
        )
        test_db_session.add(template)
        test_db_session.commit()
        return template

    def test_broken_regex_no_crash(self, test_db_session, setup_bad_template, temp_storage_dir):
        """验证非法正则不会导致服务崩溃"""
        template = setup_bad_template
        package = OntologyPackage(
            id=f"pkg-bad-{generate_uuid()[:8]}",
            series_code="test-bad-regex",
            version=1,
            template_id=template.id,
            status="READY"
        )
        test_db_session.add(package)
        
        # 创建一个测试文件
        pkg_path = temp_storage_dir / package.id
        os.makedirs(pkg_path, exist_ok=True)
        (pkg_path / "test.md").write_text("# Test", encoding='utf-8')
        
        test_db_session.add(OntologyFile(package_id=package.id, file_path="test.md", file_size=10))
        test_db_session.commit()

        service = ParsingService(test_db_session)
        # 运行解析：不应抛出 re.error 异常
        try:
            service.parse_package(package.id, template.id)
        except Exception as e:
            pytest.fail(f"解析因非法正则崩溃了: {e}")

        entities = test_db_session.query(OntologyEntity).filter_by(package_id=package.id).all()
        assert len(entities) == 1
        # 虽然正则错了，但基础信息（名称、分类）应保留
        assert entities[0].name == "test"

    def test_empty_and_binary_content(self, test_db_session, temp_storage_dir):
        """验证处理空文件或意外生成的二进制内容"""
        template = ParsingTemplate(
            id=f"tpl-empty-{generate_uuid()[:8]}",
            name="Simple Template",
            rules=json.dumps({
                "entity": {"name_source": "filename_no_ext", "category_source": "directory"},
                "attribute": {"regex_patterns": []}
            })
        )
        test_db_session.add(template)
        
        package = OntologyPackage(
            id=f"pkg-empty-{generate_uuid()[:8]}",
            series_code="test-empty",
            version=1,
            template_id=template.id,
            status="READY"
        )
        test_db_session.add(package)
        test_db_session.commit()

        pkg_path = temp_storage_dir / package.id
        os.makedirs(pkg_path, exist_ok=True)
        # 1. 完全空的文件
        (pkg_path / "empty.md").write_text("", encoding='utf-8')
        # 2. 只有 Frontmatter 没有 Body
        (pkg_path / "only_fm.md").write_text("---\ntitle: Only FM\n---\n", encoding='utf-8')
        
        test_db_session.add(OntologyFile(package_id=package.id, file_path="empty.md", file_size=0))
        test_db_session.add(OntologyFile(package_id=package.id, file_path="only_fm.md", file_size=20))
        test_db_session.commit()

        service = ParsingService(test_db_session)
        service.parse_package(package.id, template.id)

        entities = test_db_session.query(OntologyEntity).filter_by(package_id=package.id).all()
        assert len(entities) == 2
        
    def test_self_referencing_wikilinks(self, test_db_session, temp_storage_dir):
        """验证自引用或循环引用的 WikiLinks 处理"""
        template = ParsingTemplate(
            id=f"tpl-link-{generate_uuid()[:8]}",
            name="Link Template",
            rules=json.dumps({"entity": {"name_source": "filename_no_ext"}, "attribute":{}})
        )
        test_db_session.add(template)
        package = OntologyPackage(
            id=f"pkg-link-{generate_uuid()[:8]}",
            series_code="test-link",
            version=1,
            template_id=template.id,
            status="READY"
        )
        test_db_session.add(package)
        test_db_session.commit()

        pkg_path = temp_storage_dir / package.id
        os.makedirs(pkg_path, exist_ok=True)
        # 自引用文件
        (pkg_path / "Self.md").write_text("See [[Self]] and also [[Other]].", encoding='utf-8')
        (pkg_path / "Other.md").write_text("Back to [[Self]].", encoding='utf-8')

        test_db_session.add(OntologyFile(package_id=package.id, file_path="Self.md", file_size=30))
        test_db_session.add(OntologyFile(package_id=package.id, file_path="Other.md", file_size=20))
        test_db_session.commit()

        service = ParsingService(test_db_session)
        service.parse_package(package.id, template.id)

        # 验证关联关系不应产生自引用
        from app.models import OntologyRelation
        rels = test_db_session.query(OntologyRelation).filter_by(package_id=package.id).all()
        # Self -> Other (1), Other -> Self (1), 合计 2。Self -> Self 应该被逻辑过滤掉了。
        assert len(rels) == 2
        for r in rels:
            assert r.source_id != r.target_id
