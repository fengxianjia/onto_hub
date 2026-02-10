import pytest
import os
import shutil
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.services.parsing_service import ParsingService
from app.models import ParsingTemplate, OntologyPackage, OntologyFile, OntologyEntity, OntologyRelation, generate_uuid

@pytest.mark.integration
class TestParsingIntegration:
    """
    Integration tests to verify the side effects of parsing.
    Ensures that parse_package correctly populates the database.
    """
    
    @pytest.fixture
    def setup_parsing_env(self, test_db_session: Session, temp_storage_dir: Path):
        """Prepare a parsing template and a mock storage package."""
        # 1. Create a Parsing Template with basic regex rules
        template = ParsingTemplate(
            id=f"tpl-{generate_uuid()[:8]}",
            name="Integration Test Template",
            rules=json.dumps({
                "entity": {
                    "name_source": "filename_no_ext",
                    "category_source": "directory"
                },
                "attribute": {
                    "regex_patterns": [
                        {"key": "title", "pattern": r"^#\s+(.*)$"}
                    ]
                }
            })
        )
        test_db_session.add(template)
        
        # 2. Create a Package
        package = OntologyPackage(
            id=f"pkg-{generate_uuid()[:8]}",
            series_code="test-parsing",
            version=1,
            template_id=template.id,
            status="READY"
        )
        test_db_session.add(package)
        test_db_session.commit()
        
        # 3. Prepare physical files in the temp storage
        pkg_path = temp_storage_dir / package.id
        os.makedirs(pkg_path, exist_ok=True)
        
        # Create a category directory
        cat_dir = pkg_path / "Classes"
        cat_dir.mkdir()
        
        # Create a sample markdown file
        file_content = """---
title: Original Person
type: Class
---
# Person Entity
This is a test entity.
[[Address]]
"""
        md_file = cat_dir / "Person.md"
        md_file.write_text(file_content, encoding='utf-8')
        
        # Register file in DB
        file_record = OntologyFile(
            package_id=package.id,
            file_path="Classes/Person.md",
            file_size=len(file_content)
        )
        test_db_session.add(file_record)
        
        # Second file for relation
        addr_content = "# Address\nLinked entity."
        addr_file = cat_dir / "Address.md"
        addr_file.write_text(addr_content, encoding='utf-8')
        
        addr_record = OntologyFile(
            package_id=package.id,
            file_path="Classes/Address.md",
            file_size=len(addr_content)
        )
        test_db_session.add(addr_record)
        
        test_db_session.commit()
        
        return package, template

    def test_parsing_produces_entities_and_relations(self, test_db_session, setup_parsing_env):
        """Verify that parsing correctly extracts data and inserts into DB."""
        package, template = setup_parsing_env
        
        # Instantiate service (This was failing with TypeError previously)
        service = ParsingService(test_db_session)
        
        # Run parsing
        service.parse_package(package.id, template.id)
        
        # ASSERTIONS
        
        # Verify entities
        entities = test_db_session.query(OntologyEntity).filter_by(package_id=package.id).all()
        assert len(entities) == 2
        
        person = next(e for e in entities if e.name == "Person")
        assert person.category == "Classes"
        
        # Verify metadata extraction (from regex)
        metadata = json.loads(person.metadata_json)
        assert metadata["title"] == "Person Entity"
        
        address = next(e for e in entities if e.name == "Address")
        assert address.name == "Address"
        
        # Verify relations (from [[Address]] wiki link)
        relations = test_db_session.query(OntologyRelation).filter_by(package_id=package.id).all()
        assert len(relations) == 1
        assert relations[0].source_id == person.id
        assert relations[0].target_id == address.id
        assert relations[0].relation_type == "related_to"
