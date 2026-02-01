"""
Webhook Service for IssueSpotter AI Microservice

Sends moderation results back to the main backend via HTTP webhooks.
Features:
- Async HTTP calls (non-blocking)
- Automatic retry with exponential backoff
- Result caching for failed deliveries
"""

import asyncio
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import httpx
from app.config.settings import settings

logger = logging.getLogger(__name__)


# Webhook configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 30  # seconds
TIMEOUT_SECONDS = 10


@dataclass
class WebhookPayload:
    """Payload structure for webhook notifications."""
    post_id: str
    decision: str  # GREEN, YELLOW, RED
    score: float
    reason: str
    timestamp: str
    ai_decision: str
    human_decision: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class WebhookResult:
    """Result of a webhook delivery attempt."""
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0


class WebhookService:
    """
    Async webhook delivery service.
    
    Sends moderation results to the main backend and handles retries.
    """
    
    _pending_deliveries: List[Dict] = []  # Failed deliveries to retry
    
    @classmethod
    async def send_webhook(
        cls,
        url: str,
        payload: WebhookPayload,
        headers: Optional[Dict] = None
    ) -> WebhookResult:
        """
        Send a webhook notification with automatic retry.
        
        Args:
            url: Webhook endpoint URL
            payload: Data to send
            headers: Optional HTTP headers
            
        Returns:
            WebhookResult with success status and details
        """
        default_headers = {
            "Content-Type": "application/json",
            "X-Source": "issuespotter-ai",
            "X-Timestamp": datetime.utcnow().isoformat(),
        }
        
        if headers:
            default_headers.update(headers)
        
        retry_delay = INITIAL_RETRY_DELAY
        last_error = None
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    logger.info(f"Sending webhook to {url} (attempt {attempt}/{MAX_RETRIES})")
                    
                    response = await client.post(
                        url,
                        json=payload.to_dict(),
                        headers=default_headers
                    )
                    
                    if response.status_code in (200, 201, 202, 204):
                        logger.info(f"Webhook delivered successfully: {response.status_code}")
                        return WebhookResult(
                            success=True,
                            status_code=response.status_code,
                            response_body=response.text[:500],  # Truncate
                            attempts=attempt
                        )
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                        logger.warning(f"Webhook failed: {last_error}")
                        
                except httpx.TimeoutException:
                    last_error = "Request timeout"
                    logger.warning(f"Webhook timeout on attempt {attempt}")
                    
                except httpx.ConnectError:
                    last_error = "Connection refused"
                    logger.warning(f"Webhook connection failed on attempt {attempt}")
                    
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Webhook error on attempt {attempt}: {e}")
                
                # Wait before retry (exponential backoff)
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
        
        # All retries failed
        logger.error(f"Webhook delivery failed after {MAX_RETRIES} attempts: {last_error}")
        
        # Store for later retry
        cls._pending_deliveries.append({
            "url": url,
            "payload": payload.to_dict(),
            "failed_at": datetime.utcnow().isoformat(),
            "error": last_error
        })
        
        return WebhookResult(
            success=False,
            error=last_error,
            attempts=MAX_RETRIES
        )
    
    @classmethod
    async def notify_main_backend(
        cls,
        post_id: str,
        decision: str,
        score: float,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> WebhookResult:
        """
        Send moderation result to the main backend.
        
        Args:
            post_id: ID of the moderated post
            decision: GREEN, YELLOW, or RED
            score: Confidence score (0-1)
            reason: Explanation of the decision
            metadata: Additional data (image URLs, similar cases, etc.)
        """
        webhook_url = getattr(settings, 'MAIN_BACKEND_WEBHOOK_URL', None)
        
        if not webhook_url:
            logger.warning("MAIN_BACKEND_WEBHOOK_URL not configured, skipping webhook")
            return WebhookResult(
                success=False,
                error="Webhook URL not configured"
            )
        
        payload = WebhookPayload(
            post_id=post_id,
            decision=decision,
            score=score,
            reason=reason,
            timestamp=datetime.utcnow().isoformat(),
            ai_decision=decision,
            metadata=metadata
        )
        
        return await cls.send_webhook(webhook_url, payload)
    
    @classmethod
    def send_webhook_sync(
        cls,
        url: str,
        payload: WebhookPayload,
        headers: Optional[Dict] = None
    ) -> WebhookResult:
        """
        Synchronous wrapper for webhook delivery.
        
        Use this when you're not in an async context (e.g., Celery workers).
        """
        try:
            return asyncio.run(cls.send_webhook(url, payload, headers))
        except RuntimeError:
            # Already in async context, create new event loop
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(cls.send_webhook(url, payload, headers))
            finally:
                loop.close()
    
    @classmethod
    def notify_main_backend_sync(
        cls,
        post_id: str,
        decision: str,
        score: float,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> WebhookResult:
        """Synchronous wrapper for main backend notification."""
        try:
            return asyncio.run(
                cls.notify_main_backend(post_id, decision, score, reason, metadata)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    cls.notify_main_backend(post_id, decision, score, reason, metadata)
                )
            finally:
                loop.close()
    
    @classmethod
    def get_pending_deliveries(cls) -> List[Dict]:
        """Get list of failed webhook deliveries for manual retry."""
        return cls._pending_deliveries.copy()
    
    @classmethod
    async def retry_pending_deliveries(cls) -> Dict:
        """Retry all pending webhook deliveries."""
        if not cls._pending_deliveries:
            return {"retried": 0, "success": 0, "failed": 0}
        
        results = {"retried": 0, "success": 0, "failed": 0}
        remaining = []
        
        for delivery in cls._pending_deliveries:
            results["retried"] += 1
            
            payload = WebhookPayload(**delivery["payload"])
            result = await cls.send_webhook(delivery["url"], payload)
            
            if result.success:
                results["success"] += 1
            else:
                results["failed"] += 1
                remaining.append(delivery)
        
        cls._pending_deliveries = remaining
        return results
