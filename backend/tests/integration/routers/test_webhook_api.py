import pytest
import time


@pytest.mark.integration
class TestWebhookAPI:
    """Test webhook subscription and management endpoints."""
    
    def test_create_webhook_success(self, client):
        """Successfully create a new webhook subscription."""
        # Use an even more unique prefix to avoid any possible collision with hardcoded data
        uid = int(time.time() * 1000)
        name = f"cre-webhook-{uid}"
        response = client.post(
            "/api/webhooks",
            json={
                "name": name,
                "target_url": f"https://api.system-a.com/webhooks/{uid}",
                "event_type": "ontology.activated",
                "ontology_filter": f"filter-{uid}"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == name
        assert data["ontology_filter"] == f"filter-{uid}"
    
    def test_list_webhooks(self, client):
        """List all registered webhooks."""
        uid = int(time.time() * 1000)
        name = f"list-test-{uid}"
        # Create one first
        resp = client.post(
            "/api/webhooks",
            json={
                "name": name,
                "target_url": f"http://example.com/{uid}"
            }
        )
        assert resp.status_code == 201
        
        response = client.get("/api/webhooks")
        assert response.status_code == 200
        data = response.json()
        # Items might already exist from other tests, so we check if ours is present
        assert any(w["name"] == name for w in data["items"])
    
    def test_delete_webhook(self, client):
        """Register and then delete a webhook."""
        name = f"del-test-{int(time.time() * 1000)}"
        # Create
        resp = client.post(
            "/api/webhooks",
            json={"name": name, "target_url": "http://del.com"}
        )
        wh_id = resp.json()["id"]
        
        # Delete
        del_resp = client.delete(f"/api/webhooks/{wh_id}")
        assert del_resp.status_code == 204
        
        # Verify gone
        get_resp = client.get("/api/webhooks")
        assert not any(w["id"] == wh_id for w in get_resp.json()["items"])

    def test_update_webhook(self, client):
        """Update a webhook's name or URL."""
        name = f"old-{int(time.time() * 1000)}"
        new_name = f"new-{int(time.time() * 1000)}"
        # Create
        resp = client.post(
            "/api/webhooks",
            json={"name": name, "target_url": "http://old.com"}
        )
        wh_id = resp.json()["id"]
        
        # Update using PUT (as defined in main.py)
        up_resp = client.put(
            f"/api/webhooks/{wh_id}",
            json={"name": new_name, "target_url": "http://new.com"}
        )
        assert up_resp.status_code == 200
        assert up_resp.json()["name"] == new_name

    def test_get_subscriptions(self, client):
        """Test getting ontology subscription status."""
        # This will use the actual service which might hit DB
        response = client.get("/api/webhooks/subscriptions/by-code/eco")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_deliveries(self, client):
        """Test getting ontology delivery history."""
        # Use a non-existent ID or mock if needed, but here we just check route exists
        response = client.get("/api/webhooks/deliveries/invalid-id")
        # Depending on implementation, might return 404 if ID not found in HandleResult
        assert response.status_code in [200, 404]

    def test_manual_push(self, client):
        """Test manual trigger push endpoint."""
        response = client.post("/api/webhooks/push/invalid-id?webhook_id=any")
        assert response.status_code == 404  # Expected for invalid ontology ID
