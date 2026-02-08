import pytest
import os
import requests
import time

def test_delete_ontology_cleanup(client, unique_code, dummy_zip):
    # 1. Create v1 (Active)
    print(f"Creating v1 for {unique_code}")
    v1 = client.create_ontology(dummy_zip, code=unique_code, name="Delete Test")
    v1_id = v1['id']
    
    # 2. Create v2 (Active)
    print(f"Creating v2 for {unique_code}")
    v2 = client.add_version(dummy_zip, code=unique_code)
    v2_id = v2['id']
    
    # Verify both exist on disk
    # We need to know the storage path. Since tests run on same machine, we can guess.
    # storage_dir = backend/data/ontohub_storage
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend/data/ontohub_storage'))
    v1_zip = os.path.join(base_dir, f"{v1_id}.zip")
    v2_zip = os.path.join(base_dir, f"{v2_id}.zip")
    v1_dir = os.path.join(base_dir, v1_id)
    v2_dir = os.path.join(base_dir, v2_id)
    
    assert os.path.exists(v1_zip), f"v1 zip not found at {v1_zip}"
    assert os.path.exists(v2_zip), f"v2 zip not found at {v2_zip}"
    assert os.path.exists(v1_dir), f"v1 dir not found at {v1_dir}"
    assert os.path.exists(v2_dir), f"v2 dir not found at {v2_dir}"
    
    # 3. Try to delete v2 (Should fail because it is active)
    with pytest.raises(requests.exceptions.HTTPError):
        client.delete_ontology(v2_id)
        
    # 4. Activate v1
    print("Activating v1")
    client.activate_ontology(v1_id)
    
    # 5. Delete v2
    print("Deleting v2")
    client.delete_ontology(v2_id)
    
    # 6. Verify v2 is gone from disk
    assert not os.path.exists(v2_zip), "v2 zip should have been deleted"
    assert not os.path.exists(v2_dir), "v2 dir should have been deleted"
    
    # 7. Verify v1 is still there
    assert os.path.exists(v1_zip), "v1 zip should still exist"
    assert os.path.exists(v1_dir), "v1 dir should still exist"
