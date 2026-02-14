
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.integration
class TestWebhookConnectivity:
    """Test webhook connectivity check endpoint."""

    @patch("app.services.webhook_service.utils.send_webhook_request", new_callable=AsyncMock)
    def test_connectivity_check_with_url(self, mock_send, client):
        """Test with ad-hoc URL."""
        mock_send.return_value = {
            "status": "SUCCESS",
            "response_status": 200,
            "error_message": None
        }

        # Use the nested path
        response = client.post(
            "/api/webhooks/test/connection",
            json={
                "target_url": "http://test.com/hook",
                "secret_token": "my-secret"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["response_status"] == 200
        
        # Verify call arguments
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs["target_url"] == "http://test.com/hook"
        assert call_kwargs["secret_token"] == "my-secret"
        assert call_kwargs["event_type"] == "ping"
        assert call_kwargs["ontology_code"] == "SYSTEM_TEST"

    @patch("app.services.webhook_service.utils.send_webhook_request", new_callable=AsyncMock)
    def test_connectivity_check_with_id(self, mock_send, client):
        """Test with existing webhook ID."""
        # 1. Create a webhook first
        create_resp = client.post(
            "/api/webhooks",
            json={
                "name": "ConnTestHook",
                "target_url": "http://saved-url.com",
                "secret_token": "saved-secret",
                "event_type": "ontology.activated"
            }
        )
        assert create_resp.status_code == 201
        webhook_id = create_resp.json()["id"]

        # 2. Test connectivity using ID
        mock_send.return_value = {
            "status": "FAILURE",
            "response_status": 500,
            "error_message": "Internal Server Error"
        }

        response = client.post(
            "/api/webhooks/test/connection",
            json={"webhook_id": webhook_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILURE"
        assert data["response_status"] == 500

        # Verify call arguments used saved config
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs["target_url"] == "http://saved-url.com"
        assert call_kwargs["secret_token"] == "saved-secret"

    def test_connectivity_validation_error(self, client):
        """Test missing arguments."""
        response = client.post(
            "/api/webhooks/test/connection",
            json={} # Missing target_url and webhook_id
        )
        
        # Service logic returns ServiceResult.failure_result(ServiceStatus.FAILURE, ...)
        # handle_result maps ServiceStatus.FAILURE to 500
        assert response.status_code == 500
        data = response.json()
        assert "Target URL is required" in data["detail"]
