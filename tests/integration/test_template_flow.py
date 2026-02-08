import pytest
import sys
import os
import io
import zipfile
from fastapi.testclient import TestClient

# Adjust path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.main import app

client = TestClient(app)

@pytest.fixture
def valid_zip_content():
    """Creates a simple zip with a markdown file."""
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr("index.md", "# Test Entity\n\nDescription here.")
    return b.getvalue()

def test_template_flow(valid_zip_content):
    # 1. Create a Template
    tpl_data = {
        "name": "Integration Template",
        "rules": '{"attribute": {"regex_patterns": []}}' 
    }
    res = client.post("/api/templates/", json=tpl_data)
    if res.status_code != 201:
        # Template might already exist if we didn't clean DB
        print("Template creation warning:", res.json())
        # Try to use existing if name conflict, but here we likely want new ID
        # Let's assume clean DB or unique name?
        # Let's verify we got an ID.
        pass

    assert res.status_code == 201
    template_id = res.json()["id"]

    # 2. Upload v1 WITH template
    import time
    code = f"flow-test-{int(time.time())}" # Unique code
    
    files = {"file": ("test.zip", valid_zip_content, "application/zip")}
    data = {
        "code": code,
        "name": "Flow Test",
        "template_id": template_id
    }
    res_v1 = client.post("/api/ontologies", files=files, data=data)
    if res_v1.status_code != 201:
        print("v1 upload failed:", res_v1.json())
        
    assert res_v1.status_code == 201
    pkg_v1 = res_v1.json()
    assert pkg_v1["template_id"] == template_id
    assert pkg_v1["version"] == 1

    # 3. Upload v2 WITHOUT template (Inheritance)
    files_v2 = {"file": ("test_v2.zip", valid_zip_content, "application/zip")}
    # Note: endpoints/ontologies expect 'code' in path for adding version
    # data can contain custom_id, template_id
    # We DO NOT send template_id here
    res_v2 = client.post(f"/api/ontologies/{code}/versions", files=files_v2) 
    
    if res_v2.status_code != 201:
        print("v2 upload failed:", res_v2.json())

    assert res_v2.status_code == 201
    pkg_v2 = res_v2.json()
    
    # CHECK: Inheritance
    assert pkg_v2["template_id"] == template_id
    assert pkg_v2["version"] == 2
    
    print(f"Test Passed! v1_template={pkg_v1['template_id']}, v2_template={pkg_v2['template_id']}")
