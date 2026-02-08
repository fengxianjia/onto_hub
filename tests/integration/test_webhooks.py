import pytest
import time
import requests

def test_webhook_registration_and_trigger(client, unique_code, dummy_zip):
    # 1. Register Webhook
    target_url = "http://localhost:9999/test-hook"
    wh = client.subscribe_webhook(target_url, ontology_filter=unique_code)
    assert wh['id'] is not None
    assert wh['target_url'] == target_url
    assert wh['ontology_filter'] == unique_code
    
    # 2. Trigger Event (Create Ontology matching filter)
    # Note: Creating v1 triggers "ontology.activated"
    client.create_ontology(dummy_zip, code=unique_code, name="Webhook Test")
    
    # 3. Verify Subscription Status shows the webhook
    # We need to use raw requests or extend client to support status check
    # Let's use raw requests for now as client.py might ideally only cover public API
    # But for tests, we can use the client's base_url
    
    status_url = f"{client.base_url}/api/subscriptions/ontologies/status"
    resp = requests.get(status_url, params={"code": unique_code})
    assert resp.status_code == 200
    
    data = resp.json()
    # Find our webhook in the status list
    found_wh = next((item for item in data if item['webhook_id'] == wh['id']), None)
    assert found_wh is not None, "Webhook not found in status list"
    
    # Since we can't easily verify the external delivery without a mock server,
    # finding it in the status list confirms the backend linked the event to the subscription.

def test_webhook_cross_filtering_name_vs_code(client, unique_code, dummy_zip):
    """
    Verify that a webhook filtered by NAME is still visible when querying status by CODE.
    This covers the bug fix verified by verify_fixes.py.
    """
    ontology_name = f"CrossFilter-{unique_code}"
    
    # 1. Register Webhook filtered by NAME
    target_url = "http://localhost:9999/name-hook"
    wh = client.subscribe_webhook(target_url, ontology_filter=ontology_name)
    
    # 2. Create Ontology with that NAME and CODE
    client.create_ontology(dummy_zip, code=unique_code, name=ontology_name)
    
    # 3. Query Status by CODE
    # The subscription should appear because the backend should match Name OR Code
    status_url = f"{client.base_url}/api/subscriptions/ontologies/status"
    resp = requests.get(status_url, params={"code": unique_code})
    assert resp.status_code == 200
    
    data = resp.json()
    found = any(item['webhook_id'] == wh['id'] for item in data)
    assert found, "Webhook filtered by Name should be visible when querying by Code"
