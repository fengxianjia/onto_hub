import requests
import time
import os
import zipfile
import io

BASE_URL = "http://localhost:8003/api"

def create_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for path, content in files.items():
            z.writestr(path, content)
    return buf.getvalue()

def test_comparison():
    # 1. Create v1
    v1_files = {
        "keep.txt": "Line to keep\n",
        "modify.txt": "Old content\n",
        "delete.txt": "Deleted file\n"
    }
    code = f"diff_test_{int(time.time())}"
    
    print(f"Creating v1 for {code}...")
    r1 = requests.post(
        f"{BASE_URL}/ontologies",
        data={"code": code, "name": "Diff Test"},
        files={"file": ("v1.zip", create_zip(v1_files))}
    )
    if r1.status_code != 201:
        print(f"v1 creation failed: {r1.text}")
        return
    v1_id = r1.json()["id"]
    print(f"v1_id: {v1_id}")
    
    # Wait for processing
    time.sleep(1)
    
    # 2. Create v2
    v2_files = {
        "keep.txt": "Line to keep\n",
        "modify.txt": "New content\n",
        "add.txt": "Added file\n"
    }
    print("Creating v2...")
    r2 = requests.post(
        f"{BASE_URL}/ontologies/{code}/versions",
        files={"file": ("v2.zip", create_zip(v2_files))}
    )
    if r2.status_code != 201:
        print(f"v2 creation failed: {r2.text}")
        return
    v2_id = r2.json()["id"]
    print(f"v2_id: {v2_id}")
    
    time.sleep(1)
    
    # Check if they exist in list
    print("Listing ontologies to verify existence...")
    r_list = requests.get(f"{BASE_URL}/ontologies", params={"code": code, "all_versions": "true"})
    print(f"Found in list: {[p['id'] for p in r_list.json()]}")
    
    # 3. Compare
    print(f"Comparing {v1_id} (base) and {v2_id} (target)...")
    r_comp = requests.get(
        f"{BASE_URL}/ontologies/compare",
        params={"base_id": v1_id, "target_id": v2_id}
    )
    
    if r_comp.status_code != 200:
        print(f"FAILED: {r_comp.text}")
        return
    
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
    
    print("SUCCESS: Comparison logic verified!")

if __name__ == "__main__":
    test_comparison()
