import os
# Set environment to 'test' BEFORE anything else to ensure early configuration loads correctly
os.environ["APP_ENV"] = "test"

from app.config import settings
# Explicitly force settings to reload so it picks up APP_ENV=test even if it was imported early
settings.reload()

import shutil
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app, get_db
from app.database import Base
from app import models
from app.repositories.ontology_repo import OntologyRepository
from app.repositories.webhook_repo import WebhookRepository
from app.services.ontology_service import OntologyService
from app.services.webhook_service import WebhookService
from app.config import settings


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_setup():
    """Ensure the database schema is created for the test engine."""
    from app.database import get_engine, Base
    engine = get_engine()
    # Ensure we are using an in-memory database for tests
    assert str(engine.url) == "sqlite:///:memory:", f"CRITICAL: Test engine binding to PRODUCTION? {engine.url}"
    
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db_session(test_db_setup):
    """Get a session from the standard app factory."""
    from app.database import SessionLocal
    # In test mode, SessionLocal is already bound to the in-memory engine
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override the FastAPI dependency to use the test session."""
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

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_storage():
    """Final cleanup of the base test storage directory after all tests."""
    yield
    # Safely clear the test storage base directory
    from app.config import settings
    base_test_dir = Path(settings.BASE_DIR) / "tests" / "test_storage"
    if base_test_dir.exists() and "test_storage" in str(base_test_dir):
        try:
            shutil.rmtree(base_test_dir)
        except Exception:
            pass

@pytest.fixture(scope="function")
def temp_storage_dir(monkeypatch):
    """
    Create a fresh, unique storage directory for each test run
    to avoid any cross-test state leakage, and cleanup after.
    """
    from app.config import settings
    base_test_dir = Path(settings.BASE_DIR) / "tests" / "test_storage"
    os.makedirs(base_test_dir, exist_ok=True)
    
    unique_run_dir = base_test_dir / f"run_{datetime.now().strftime('%H%M%S_%f')}"
    os.makedirs(unique_run_dir, exist_ok=True)
    
    # Sync global settings with this directory
    monkeypatch.setattr(settings, "STORAGE_DIR", str(unique_run_dir))
    
    yield unique_run_dir
    
    # Automatic cleanup after test finishes
    if unique_run_dir.exists():
        try:
            shutil.rmtree(unique_run_dir)
        except Exception:
            pass


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
def ontology_service(ontology_repo, webhook_repo, webhook_service, temp_storage_dir):
    return OntologyService(ontology_repo, webhook_repo, webhook_service, storage_dir=str(temp_storage_dir))


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
