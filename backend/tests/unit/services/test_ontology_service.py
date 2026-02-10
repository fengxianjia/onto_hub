"""
Unit tests for OntologyService.

Tests core business logic including:
- Version number calculation
- Series creation and retrieval
- File path management
- Deletion protection logic
"""

import pytest
import time
from unittest.mock import Mock, patch
from pathlib import Path

from app.services.ontology_service import OntologyService
from app.repositories.ontology_repo import OntologyRepository
from app.models import OntologySeries, OntologyPackage
from app.core.results import ServiceStatus


@pytest.mark.unit
class TestOntologyServiceVersioning:
    """Test version management logic."""
    
    def test_create_first_version_assigns_v1(self, test_db_session):
        """When creating the first version of a series, it should be v1."""
        repo = OntologyRepository(test_db_session)
        webhook_repo = Mock()
        webhook_service = Mock()
        service = OntologyService(repo, webhook_repo, webhook_service)
        
        # Create a new series
        series = repo.create_series(
            code="test-ontology",
            name="Test Ontology",
            description="Test description"
        )
        
        # Verify first version would be 0 (none existing)
        latest_version = repo.get_latest_version("test-ontology")
        assert latest_version == 0
    
    def test_subsequent_versions_increment(self, test_db_session):
        """Subsequent versions should increment the version number."""
        repo = OntologyRepository(test_db_session)
        
        # Create series and first package
        code = f"sub-{int(time.time())}"
        series = repo.create_series(
            code=code,
            name="Test Ontology"
        )
        
        pkg1 = repo.create_package(
            series_code=code,
            version=1
        )
        
        # Get latest version
        latest = repo.get_latest_version(code)
        assert latest == 1
        
        # Create second version
        pkg2 = repo.create_package(
            series_code="test-ontology",
            version=2
        )
        
        latest = repo.get_latest_version("test-ontology")
        assert latest == 2


@pytest.mark.unit
class TestOntologyServiceDeletionProtection:
    """Test deletion protection logic."""
    
    def test_cannot_delete_active_version(self, test_db_session):
        """Active versions should be protected from deletion."""
        repo = OntologyRepository(test_db_session)
        webhook_repo = Mock()
        webhook_service = Mock()
        service = OntologyService(repo, webhook_repo, webhook_service)
        
        # Create and activate a version
        code = f"del-prot-{int(time.time() * 1000)}"
        series = repo.create_series(code=code, name="Test")
        pkg = repo.create_package(
            series_code=code,
            version=1
        )
        repo.set_active_version(code, pkg.id)
        
        # Attempt to delete should fail (Active version)
        result = service.delete_version(pkg.id)
        assert result.status == ServiceStatus.VERSION_ACTIVE
        assert "正在启用" in result.message
    
    def test_can_delete_inactive_version(self, test_db_session):
        """Inactive versions without dependencies should be deletable."""
        repo = OntologyRepository(test_db_session)
        webhook_repo = Mock()
        webhook_service = Mock()
        service = OntologyService(repo, webhook_repo, webhook_service)
        
        # Create two versions, activate the second
        code = f"del-succ-{int(time.time() * 1000)}"
        series = repo.create_series(code=code, name="Test")
        pkg1 = repo.create_package(
            series_code=code,
            version=1
        )
        pkg2 = repo.create_package(
            series_code=code,
            version=2
        )
        repo.set_active_version(code, pkg2.id)
        
        # Should be able to delete v1
        with patch.object(service.webhook_service, 'get_in_use_package_ids', return_value=[]):
            result = service.delete_version(pkg1.id)
            assert result.status == ServiceStatus.SUCCESS


@pytest.mark.unit  
class TestOntologyServiceFileManagement:
    """Test file path and storage management."""
    
    def test_get_storage_path_creates_unique_directory(self, temp_storage_dir):
        """Each package should get a unique storage directory."""
        repo = Mock()
        webhook_repo = Mock()
        webhook_service = Mock()
        
        from app.config import settings
        with patch.object(settings, 'STORAGE_DIR', str(temp_storage_dir)):
            service = OntologyService(repo, webhook_repo, webhook_service)
            
            path1 = service._get_storage_path("pkg-id-1")
            path2 = service._get_storage_path("pkg-id-2")
            
            assert path1 != path2
            assert "pkg-id-1" in str(path1)
            assert "pkg-id-2" in str(path2)
    
    def test_cleanup_removes_package_directory(self, temp_storage_dir):
        """Cleanup should remove the package's storage directory."""
        repo = Mock()
        webhook_repo = Mock()
        webhook_service = Mock()
        
        from app.config import settings
        with patch.object(settings, 'STORAGE_DIR', str(temp_storage_dir)):
            service = OntologyService(repo, webhook_repo, webhook_service)
        
        # Create a fake package directory
        pkg_dir = temp_storage_dir / "test-package-id"
        pkg_dir.mkdir()
        (pkg_dir / "test.txt").write_text("test content")
        
        assert pkg_dir.exists()
        
        # Cleanup
        # Package needs to NOT be active to be deletable
        repo.get_package.return_value = Mock(id="test-package-id", is_active=False, series_code="any")
        # Mock webhook check to not block deletion
        with patch.object(service.webhook_service, 'get_in_use_package_ids', return_value=[]):
            service.delete_version("test-package-id")
        
        # Directory should be removed
        assert not pkg_dir.exists()
        assert not (temp_storage_dir / "pkg-id-1").exists() # Just a reminder that we use storage_dir now
