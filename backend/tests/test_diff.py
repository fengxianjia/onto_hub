import pytest
import time
import zipfile
import io

def create_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for path, content in files.items():
            z.writestr(path, content)
    return buf.getvalue()

@pytest.mark.integration
def test_comparison(client):
    # 1. Create v1
    v1_files = {
        "keep.txt": "Line to keep\n",
        "modify.txt": "Old content\n",
        "delete.txt": "Deleted file\n"
    }
    code = f"diff_test_{int(time.time() * 1000)}"
    
    r1 = client.post(
        "/api/ontologies?is_initial=true",
        data={"code": code, "name": f"Diff Test {code}"},
        files={"file": ("v1.zip", create_zip(v1_files))}
    )
    assert r1.status_code == 201
    v1_id = r1.json()["id"]
    
    # 2. Create v2 (automatically increments version to 2)
    v2_files = {
        "keep.txt": "Line to keep\n",
        "modify.txt": "New content\n",
        "add.txt": "Added file\n"
    }
    r2 = client.post(
        f"/api/ontologies/{code}/versions",
        files={"file": ("v2.zip", create_zip(v2_files))}
    )
    assert r2.status_code == 201
    v2_id = r2.json()["id"]
    
    # 3. Compare
    r_comp = client.get(
        "/api/ontologies/compare",
        params={"base_id": v1_id, "target_id": v2_id}
    )
    
    assert r_comp.status_code == 200
    
    data = r_comp.json()
    files = {f["file_path"]: f for f in data["files"]}
    
    # Checks
    assert files["add.txt"]["status"] == "added"
    assert files["add.txt"]["target_content"] == "Added file\n"
    
    assert files["delete.txt"]["status"] == "deleted"
    assert files["delete.txt"]["base_content"] == "Deleted file\n"
    
    assert files["modify.txt"]["status"] == "modified"
    assert files["modify.txt"]["base_content"] == "Old content\n"
    assert files["modify.txt"]["target_content"] == "New content\n"
    
    assert files["keep.txt"]["status"] == "unchanged"
