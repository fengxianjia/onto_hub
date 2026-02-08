import pytest
import sys
import os

# Add backend to path so we can import client
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from client import OntologyClient

BASE_URL = "http://localhost:8003"

@pytest.fixture(scope="session")
def client():
    """Returns an OntologyClient instance connected to the running server."""
    return OntologyClient(BASE_URL)

@pytest.fixture
def unique_code():
    """Returns a unique ontology code based on timestamp.""" 
    import time
    return f"pytest-{int(time.time()*1000)}"

@pytest.fixture
def dummy_zip(tmp_path):
    """Creates a temporary zip file and returns its path."""
    import zipfile
    p = tmp_path / "test.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("README.md", "Test content")
    return str(p)
