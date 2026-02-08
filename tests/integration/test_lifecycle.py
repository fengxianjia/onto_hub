import pytest

def test_ontology_lifecycle(client, unique_code, dummy_zip):
    # 1. Create Series
    print(f"Creating ontology with code: {unique_code}")
    res = client.create_ontology(dummy_zip, code=unique_code, name="Test Ontology")
    assert res['code'] == unique_code
    assert res['version'] == 1
    assert 'id' in res
    
    # 2. List (Active)
    # The newly created one should be in the list
    items = client.get_ontologies()
    found = any(i['code'] == unique_code and i['version'] == 1 for i in items)
    assert found, f"Created ontology {unique_code} not found in active list"

    # 3. Add Version
    res2 = client.add_version(dummy_zip, code=unique_code)
    assert res2['code'] == unique_code
    assert res2['version'] == 2
    assert res2['id'] != res['id'], "New version should have different ID"
    # Verify Name Inheritance (Regression Test)
    # create_ontology used `unique_code` as the name in step 1.
    # add_version with no name should preserve that name.
    assert res2['name'] == "Test Ontology", f"Expected 'Test Ontology', got '{res2['name']}'"

    # 4. List History
    history = client.get_ontologies(code=unique_code, all_versions=True)
    versions = sorted([i['version'] for i in history])
    assert versions == [1, 2], f"Expected history [1, 2], got {versions}"

def test_create_duplicate_code_fails(client, unique_code, dummy_zip):
    # Create first time
    client.create_ontology(dummy_zip, code=unique_code, name="Original")
    
    # Create second time with same code (should fail or error)
    # The client method raises HTTPError on non-200.
    # We expect 400 Bad Request if code exists.
    import requests
    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        client.create_ontology(dummy_zip, code=unique_code, name="Duplicate")
    
    assert excinfo.value.response.status_code == 400

def test_version_name_inheritance(client, unique_code, dummy_zip):
    """验证新增版本时，能正确继承前一个版本的名称"""
    series_name = f"InheritTest-{unique_code}"
    
    # 1. 创建 v1，设置明确的名称
    client.create_ontology(dummy_zip, code=unique_code, name=series_name)
    
    # 2. 新增 v2，不传递名称
    res_v2 = client.add_version(dummy_zip, code=unique_code)
    
    # 3. 验证 v2 继承了 v1 的名称，而不是默认使用文件名
    assert res_v2['name'] == series_name
    assert res_v2['version'] == 2

def test_ontology_comparison(client, unique_code, tmp_path):
    import zipfile

    def create_zip_file(files, name):
        p = tmp_path / name
        with zipfile.ZipFile(p, 'w') as z:
            for path, content in files.items():
                z.writestr(path, content)
        return str(p)

    # 1. Create v1
    v1_files = {"keep.txt": "Line to keep\n", "modify.txt": "Old content\n", "delete.txt": "Redundant\n"}
    v1_path = create_zip_file(v1_files, "v1.zip")
    r1 = client.create_ontology(v1_path, code=unique_code, name="Diff Test")
    v1_id = r1['id']
    
    # 2. Create v2
    v2_files = {"keep.txt": "Line to keep\n", "modify.txt": "New content\n", "add.txt": "New file\n"}
    v2_path = create_zip_file(v2_files, "v2.zip")
    r2 = client.add_version(v2_path, code=unique_code)
    v2_id = r2['id']
    
    # 3. Compare
    import requests
    r_comp = requests.get(
        f"{client.base_url}/api/ontologies/compare",
        params={"base_id": v1_id, "target_id": v2_id}
    )
    r_comp.raise_for_status()
    data = r_comp.json()
    files = {f["file_path"]: f for f in data["files"]}
    
    assert files["add.txt"]["status"] == "added"
    assert files["add.txt"]["target_content"] == "New file\n"
    assert files["delete.txt"]["status"] == "deleted"
    assert files["modify.txt"]["status"] == "modified"
    assert files["modify.txt"]["target_content"] == "New content\n"
    assert files["keep.txt"]["status"] == "unchanged"
