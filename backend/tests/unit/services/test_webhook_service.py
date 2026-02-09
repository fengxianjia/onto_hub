"""
Unit tests for WebhookService.

Tests:
- Payload generation
- Filtering logic
- Event dispatching
"""

import pytest
from unittest.mock import Mock, patch
from app.services.webhook_service import WebhookService
from app.models import Webhook, OntologyPackage
from app.core.results import ServiceStatus


@pytest.mark.unit
class TestWebhookServiceBehavior:
    """Test webhook service behavior using public interfaces."""
    
    def test_broadcast_event_filters_webhooks(self):
        """Webhooks should be selected based on the event type and ontology name."""
        repo = Mock()
        service = WebhookService(repo)
        background_tasks = Mock()
        
        # Scenario: Two webhooks, one matches the event
        wh1 = Mock(spec=Webhook)
        wh1.id = "wh-1"
        wh1.target_url = "http://a.com"
        wh1.secret_token = "secret1"
        
        repo.get_webhooks_by_event.return_value = [wh1]
        
        payload = {"test": "data"}
        service.broadcast_event(
            event_type="ontology.activated",
            payload=payload,
            ontology_name="test-onto",
            background_tasks=background_tasks
        )
        
        # Verify repository was queried correctly
        repo.get_webhooks_by_event.assert_called_once_with("ontology.activated", ontology_name="test-onto")
        
        # Verify background task was added
        background_tasks.add_task.assert_called_once()
        args, kwargs = background_tasks.add_task.call_args
        # The first arg should be the broadcast function, the second is the requests list
        assert len(args) >= 2
        webhook_requests = args[1]
        assert len(webhook_requests) == 1
        assert webhook_requests[0]["target_url"] == "http://a.com"
        assert webhook_requests[0]["payload"] == payload

    @patch('app.services.webhook_service.utils.time.time', return_value=123456789)
    def test_get_in_use_package_ids_extracts_from_delivery(self, mock_time):
        """Test package usage detection logic."""
        repo = Mock()
        service = WebhookService(repo)
        
        wh = Mock(spec=Webhook)
        wh.id = "wh-1"
        repo.get_webhooks_by_event.return_value = [wh]
        
        delivery = Mock()
        import json
        delivery.payload = json.dumps({"id": "pkg-123", "version": 1})
        repo.get_latest_success_delivery.return_value = delivery
        
        in_use = service.get_in_use_package_ids("onto-code")
        
        assert "pkg-123" in in_use
        repo.get_webhooks_by_event.assert_called_with("ontology.activated", ontology_code="onto-code")
