"""
Global test fixtures and configuration for pytest.

This module provides:
- Database session fixtures (in-memory SQLite for isolation)
- FastAPI test client fixtures
- Temporary directory fixtures for file operations
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import Base, get_db
from app.repositories.ontology_repo import OntologyRepository
from app.repositories.webhook_repo import WebhookRepository
from app.services.ontology_service import OntologyService
from app.services.webhook_service import WebhookService


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """Create an in-memory SQLite database engine for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a database session that rolls back after each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override the FastAPI dependency to use test database."""
    def _override():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def client(override_get_db):
    """Synchronous test client for FastAPI."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
async def async_client(override_get_db):
    """Async test client for FastAPI (for async endpoint testing)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def temp_storage_dir():
    """
    Create a temporary directory for file operations.
    Automatically cleaned up after test completion.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="ontohub_test_"))
    yield temp_dir
    # Cleanup: Remove all files and the directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def ontology_repo(test_db_session):
    return OntologyRepository(test_db_session)


@pytest.fixture(scope="function")
def webhook_repo(test_db_session):
    return WebhookRepository(test_db_session)


@pytest.fixture(scope="function")
def webhook_service(webhook_repo):
    return WebhookService(webhook_repo)


@pytest.fixture(scope="function")
def ontology_service(ontology_repo, webhook_repo, webhook_service):
    return OntologyService(ontology_repo, webhook_repo, webhook_service)


@pytest.fixture(scope="function")
def sample_ontology_zip(temp_storage_dir):
    """
    Create a sample ontology ZIP file for testing uploads.
    Returns the path to the ZIP file.
    """
    import zipfile
    
    # Create a simple ontology structure
    ontology_dir = temp_storage_dir / "sample_ontology"
    ontology_dir.mkdir()
    
    # Create sample files
    (ontology_dir / "README.md").write_text("# Sample Ontology\\n\\nThis is a test.")
    (ontology_dir / "schema.owl").write_text('<?xml version="1.0"?>\n<Ontology/>')
    
    # Create ZIP
    zip_path = temp_storage_dir / "sample_ontology.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in ontology_dir.rglob("*"):
            if file.is_file():
                zipf.write(file, file.relative_to(ontology_dir))
    
    return zip_path
