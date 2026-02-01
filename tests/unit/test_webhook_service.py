"""
Unit Tests for Webhook Service

Tests webhook delivery, retry logic, and payload structure.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


class TestWebhookPayload:
    """Test WebhookPayload dataclass."""
    
    def test_payload_creation(self):
        """Test creating webhook payload."""
        from app.services.webhook_service import WebhookPayload
        
        payload = WebhookPayload(
            post_id="test-123",
            decision="GREEN",
            score=0.1,
            reason="Content is safe",
            timestamp=datetime.utcnow().isoformat(),
            ai_decision="GREEN"
        )
        
        assert payload.post_id == "test-123"
        assert payload.decision == "GREEN"
        assert payload.score == 0.1
    
    def test_payload_to_dict(self):
        """Test converting payload to dictionary."""
        from app.services.webhook_service import WebhookPayload
        
        payload = WebhookPayload(
            post_id="test-123",
            decision="YELLOW",
            score=0.5,
            reason="Needs review",
            timestamp="2026-02-01T12:00:00",
            ai_decision="YELLOW",
            human_decision=None,
            metadata={"source": "test"}
        )
        
        d = payload.to_dict()
        
        assert d["post_id"] == "test-123"
        assert d["decision"] == "YELLOW"
        assert d["metadata"] == {"source": "test"}
        assert d["human_decision"] is None


class TestWebhookResult:
    """Test WebhookResult dataclass."""
    
    def test_successful_result(self):
        """Test successful webhook result."""
        from app.services.webhook_service import WebhookResult
        
        result = WebhookResult(
            success=True,
            status_code=200,
            response_body="OK",
            attempts=1
        )
        
        assert result.success is True
        assert result.status_code == 200
        assert result.attempts == 1
        assert result.error is None
    
    def test_failed_result(self):
        """Test failed webhook result."""
        from app.services.webhook_service import WebhookResult
        
        result = WebhookResult(
            success=False,
            error="Connection refused",
            attempts=3
        )
        
        assert result.success is False
        assert result.error == "Connection refused"
        assert result.attempts == 3


class TestWebhookConstants:
    """Test webhook configuration constants."""
    
    def test_retry_settings(self):
        """Test retry configuration."""
        from app.services.webhook_service import (
            MAX_RETRIES, 
            INITIAL_RETRY_DELAY, 
            MAX_RETRY_DELAY, 
            TIMEOUT_SECONDS
        )
        
        assert MAX_RETRIES == 3
        assert INITIAL_RETRY_DELAY == 1
        assert MAX_RETRY_DELAY == 30
        assert TIMEOUT_SECONDS == 10


class TestWebhookServiceStorage:
    """Test pending delivery storage."""
    
    def test_get_pending_deliveries_empty(self):
        """Test getting pending deliveries when none exist."""
        from app.services.webhook_service import WebhookService
        
        # Clear any existing pending
        WebhookService._pending_deliveries = []
        
        pending = WebhookService.get_pending_deliveries()
        assert isinstance(pending, list)
