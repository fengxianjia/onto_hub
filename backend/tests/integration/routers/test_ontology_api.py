import pytest
import time


@pytest.mark.integration
@pytest.mark.integration
class TestOntologyUploadAPI:
    """Test ontology upload and creation endpoints."""
    
    def test_create_ontology_success(self, client, sample_ontology_zip):
        """Successfully upload a new ontology."""
        code = f"uni-test-{int(time.time() * 1000)}"
        name = f"Onto {int(time.time() * 1000)}"
        with open(sample_ontology_zip, 'rb') as f:
            response = client.post(
                f"/api/ontologies?is_initial=true",
                data={
                    "code": code,
                    "name": name,
                    "description": "Test description"
                },
                files={"file": ("ontology.zip", f, "application/zip")}
            )
        
        assert response.status_code == 201, f"Failed: {response.json()}"
        data = response.json()
        assert data["code"] == code
        assert data["version"] == 1

    def test_create_ontology_duplicate_code_increments_version(self, client, sample_ontology_zip):
        """Uploading the same code should create a new version."""
        code = f"dupl-{int(time.time() * 1000)}"
        name = f"Name {code}"
        
        # First upload (Initial)
        with open(sample_ontology_zip, 'rb') as f1:
            resp1 = client.post(
                "/api/ontologies?is_initial=true",
                data={"code": code, "name": name},
                files={"file": ("v1.zip", f1, "application/zip")}
            )
            assert resp1.status_code == 201, f"Initial upload failed: {resp1.json()}"
        
        # Second upload with same code
        with open(sample_ontology_zip, 'rb') as f2:
            resp2 = client.post(
                f"/api/ontologies/{code}/versions",
                files={"file": ("v2.zip", f2, "application/zip")}
            )
        assert resp2.status_code == 201, f"Version upload failed: {resp2.json()}"
        assert resp2.json()["version"] == 2


@pytest.mark.integration
class TestOntologyDeletionAPI:
    """Test ontology deletion endpoints and protection."""
    
    def test_delete_inactive_version_success(self, client, sample_ontology_zip):
        """Delete an inactive version."""
        code = f"vdel-succ-{int(time.time() * 1000)}"
        name = f"Del Test {code}"
        # Create version 1
        with open(sample_ontology_zip, 'rb') as f:
            resp1 = client.post(
                "/api/ontologies?is_initial=true",
                data={"code": code, "name": name},
                files={"file": ("v1.zip", f, "application/zip")}
            )
        assert resp1.status_code == 201, f"Initial creation failed: {resp1.json()}"
        pkg1_id = resp1.json()["id"]
        
        # Create version 2 (automatically activated)
        with open(sample_ontology_zip, 'rb') as f:
            resp2 = client.post(
                f"/api/ontologies/{code}/versions",
                files={"file": ("v2.zip", f, "application/zip")}
            )
        assert resp2.status_code == 201, f"Version creation failed: {resp2.json()}"
        
        # Delete v1 should succeed because v2 is active
        del_resp = client.delete(f"/api/ontologies/{pkg1_id}")
        assert del_resp.status_code == 204
    
    def test_delete_active_version_fails(self, client, sample_ontology_zip):
        """Cannot delete the active version."""
        code = f"vdel-fail-{int(time.time() * 1000)}"
        name = f"Active Del {code}"
        # Create (v1 is active)
        with open(sample_ontology_zip, 'rb') as f:
            resp = client.post(
                "/api/ontologies?is_initial=true",
                data={"code": code, "name": name},
                files={"file": ("test.zip", f, "application/zip")}
            )
        assert resp.status_code == 201
        pkg_id = resp.json()["id"]
        
        # Attempt to delete
        del_resp = client.delete(f"/api/ontologies/{pkg_id}")
        assert del_resp.status_code == 400


@pytest.mark.integration
class TestOntologyListAPI:
    """Test ontology listing and retrieval endpoints."""
    
    def test_list_ontologies_contains_created(self, client, sample_ontology_zip):
        """List should return at least the one we just created."""
        code = f"list-uni-{int(time.time() * 1000)}"
        name = f"List Test {code}"
        with open(sample_ontology_zip, 'rb') as f:
            resp = client.post(
                "/api/ontologies?is_initial=true",
                data={"code": code, "name": name},
                files={"file": ("test.zip", f, "application/zip")}
            )
            assert resp.status_code == 201, f"Initial creation failed: {resp.json()}"
        
        response = client.get("/api/ontologies")
        assert response.status_code == 200
        data = response.json()
        assert any(item["code"] == code for item in data["items"])


@pytest.mark.integration
class TestOntologyUpdateAPI:
    """Test ontology metadata update endpoints."""
    
    def test_update_series_metadata(self, client, sample_ontology_zip):
        """Update ontology series name and description."""
        code = f"upd-{int(time.time() * 1000)}"
        name = f"Original Name {code}"
        # Create ontology
        with open(sample_ontology_zip, 'rb') as f:
            resp = client.post(
                "/api/ontologies?is_initial=true",
                data={"code": code, "name": name},
                files={"file": ("test.zip", f, "application/zip")}
            )
            assert resp.status_code == 201, f"Initial creation failed: {resp.json()}"
        
        # Update metadata
        update_resp = client.patch(
            f"/api/ontologies/{code}",
            json={
                "name": "Updated Name",
                "description": "New description"
            }
        )
        assert update_resp.status_code == 200
        # Production returns package info on patch
        assert update_resp.json()["name"] == "Updated Name"


@pytest.mark.integration
class TestOntologyDeletionAPI:
    """Test ontology deletion endpoints and protection."""
    
    def test_delete_inactive_version_success(self, client, sample_ontology_zip):
        """Delete an inactive version."""
        code = f"del-succ-{int(time.time() * 1000)}"
        name = f"Del Test {code}"
        # Create version 1
        with open(sample_ontology_zip, 'rb') as f:
            resp1 = client.post(
                "/api/ontologies?is_initial=true",
                data={"code": code, "name": name},
                files={"file": ("v1.zip", f, "application/zip")}
            )
        assert resp1.status_code == 201, f"Initial creation failed: {resp1.json()}"
        pkg1_id = resp1.json()["id"]
        
        # Create version 2 (automatically activated)
        with open(sample_ontology_zip, 'rb') as f:
            resp2 = client.post(
                f"/api/ontologies/{code}/versions",
                files={"file": ("v2.zip", f, "application/zip")}
            )
        pkg2_id = resp2.json()["id"]
        
        # Delete v1 should succeed because v2 is active
        del_resp = client.delete(f"/api/ontologies/{pkg1_id}")
        assert del_resp.status_code == 204
    
    def test_delete_active_version_fails(self, client, sample_ontology_zip):
        """Cannot delete the active version."""
        code = f"del-fail-{int(time.time() * 1000)}"
        name = f"Active Del {code}"
        # Create (v1 is active)
        with open(sample_ontology_zip, 'rb') as f:
            create_resp = client.post(
                "/api/ontologies?is_initial=true",
                data={"code": code, "name": name},
                files={"file": ("test.zip", f, "application/zip")}
            )
        assert create_resp.status_code == 201, f"Creation failed: {create_resp.json()}"
        pkg_id = create_resp.json()["id"]
        
        # Attempt to delete
        del_resp = client.delete(f"/api/ontologies/{pkg_id}")
        # handle_result throws 400 for VERSION_ACTIVE
        assert del_resp.status_code == 400
@pytest.mark.integration
class TestOntologyReparseAPI:
    """Test the manual re-parsing endpoint."""

    def test_reparse_ontology_no_template_fails(self, client, sample_ontology_zip):
        """Should fail if no template is associated and none provided."""
        code = f"reparse-fail-{int(time.time() * 1000)}"
        # Create without template
        with open(sample_ontology_zip, 'rb') as f:
            resp = client.post(
                "/api/ontologies?is_initial=true",
                data={"code": code, "name": "No Template Onto"},
                files={"file": ("test.zip", f, "application/zip")}
            )
        pkg_id = resp.json()["id"]

        # Attempt to reparse without specifying template
        response = client.post(f"/api/ontologies/packages/{pkg_id}/reparse")
        assert response.status_code == 400
        assert "No parsing template associated" in response.json()["detail"]

    def test_reparse_ontology_success(self, client, sample_ontology_zip):
        """Successfully trigger re-parsing (Success means 200 message returned)."""
        # 1. Create a template first
        tpl_name = f"Tpl-{int(time.time())}"
        tpl_resp = client.post("/api/templates/", json={
            "name": tpl_name,
            "parser_type": "markdown",
            "rules": "{}"
        })
        tpl_id = tpl_resp.json()["id"]

        # 2. Upload ontology
        code = f"reparse-ok-{int(time.time() * 1000)}"
        with open(sample_ontology_zip, 'rb') as f:
            client.post(
                "/api/ontologies?is_initial=true",
                data={"code": code, "name": "Reparse Target", "template_id": tpl_id},
                files={"file": ("test.zip", f, "application/zip")}
            )
        
        # Get latest package
        pkg_resp = client.get(f"/api/ontologies")
        pkg = next(p for p in pkg_resp.json()["items"] if p["code"] == code)
        pkg_id = pkg["id"]

        # 3. Trigger reparse
        reparse_resp = client.post(f"/api/ontologies/packages/{pkg_id}/reparse")
        
        # This is where the ResponseValidationError happened before!
        # Now it should return 200 with the message dictionary.
        assert reparse_resp.status_code == 200
        data = reparse_resp.json()
        assert data["message"] == "Parsing task triggered"
        assert data["template_id"] == tpl_id
