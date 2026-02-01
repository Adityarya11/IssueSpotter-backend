"""
Moderator Dashboard API for IssueSpotter AI

Provides endpoints for human moderators to:
- View posts in the YELLOW bucket (needs review)
- Approve or reject posts with feedback
- View moderation statistics
- Train the AI through corrections

This is the "God Mode" dashboard for developers/moderators.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.services.vector_service import VectorService
from app.services.webhook_service import WebhookService, WebhookPayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Moderator Dashboard"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ModerationDecision(BaseModel):
    """Human moderator's decision on a post."""
    issue_id: str = Field(..., description="ID of the post being reviewed")
    decision: str = Field(..., description="APPROVE or REJECT")
    notes: Optional[str] = Field(None, description="Moderator's notes/reason")


class ModerationStats(BaseModel):
    """Dashboard statistics."""
    pending_reviews: int
    approved_today: int
    rejected_today: int
    total_processed: int


class PendingReview(BaseModel):
    """Post waiting for human review."""
    issue_id: str
    title: str
    description: str
    ai_decision: str
    ai_score: float
    timestamp: str
    image_url: Optional[str] = None
    similar_cases: List[dict] = []


class ReviewResponse(BaseModel):
    """Response after submitting a review."""
    success: bool
    message: str
    issue_id: str
    decision: str
    webhook_sent: bool = False


# ============================================================================
# Dashboard Endpoints
# ============================================================================

@router.get("/pending", response_model=List[PendingReview])
async def get_pending_reviews(
    limit: int = Query(50, ge=1, le=200, description="Max items to return")
):
    """
    Get posts that need human review (YELLOW bucket).
    
    Returns posts where AI decision is YELLOW/ESCALATE and no human
    decision has been recorded yet.
    """
    try:
        pending = VectorService.get_pending_reviews(limit=limit)
        
        reviews = []
        for item in pending:
            reviews.append(PendingReview(
                issue_id=item.get("issue_id", ""),
                title=item.get("title", ""),
                description=item.get("description", ""),
                ai_decision=item.get("ai_decision", "YELLOW"),
                ai_score=item.get("ai_score", 0.0),
                timestamp=item.get("timestamp", ""),
                image_url=item.get("image_url"),
            ))
        
        return reviews
        
    except Exception as e:
        logger.error(f"Failed to get pending reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review", response_model=ReviewResponse)
async def submit_review(decision: ModerationDecision):
    """
    Submit a human moderation decision.
    
    This is the core HITL endpoint:
    1. Stores the human decision in vector DB
    2. Notifies the main backend via webhook
    3. The AI learns from this feedback for future decisions
    """
    if decision.decision not in ("APPROVE", "REJECT"):
        raise HTTPException(
            status_code=400,
            detail="Decision must be 'APPROVE' or 'REJECT'"
        )
    
    try:
        # 1. Update the embedding with human decision
        success = VectorService.update_human_decision(
            issue_id=decision.issue_id,
            human_decision=decision.decision,
            moderator_notes=decision.notes
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Issue {decision.issue_id} not found in vector database"
            )
        
        # 2. Send webhook to main backend
        webhook_sent = False
        try:
            result = await WebhookService.notify_main_backend(
                post_id=decision.issue_id,
                decision=decision.decision,
                score=1.0,  # Human decisions are 100% confidence
                reason=decision.notes or f"Human moderator: {decision.decision}",
                metadata={"source": "human_review"}
            )
            webhook_sent = result.success
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
        
        logger.info(f"Human review submitted: {decision.issue_id} -> {decision.decision}")
        
        return ReviewResponse(
            success=True,
            message=f"Review recorded successfully",
            issue_id=decision.issue_id,
            decision=decision.decision,
            webhook_sent=webhook_sent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ModerationStats)
async def get_dashboard_stats():
    """
    Get moderation statistics for the dashboard.
    
    Shows counts of pending, approved, and rejected posts.
    """
    try:
        # Get pending count
        pending = VectorService.get_pending_reviews(limit=1000)
        
        # TODO: Add proper stats tracking
        # For now, return pending count and placeholders
        return ModerationStats(
            pending_reviews=len(pending),
            approved_today=0,  # Would need time-based query
            rejected_today=0,  # Would need time-based query
            total_processed=0   # Would need separate counter
        )
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_review_history(
    limit: int = Query(50, ge=1, le=200),
    decision_filter: Optional[str] = Query(None, description="Filter by APPROVE or REJECT")
):
    """
    Get history of human-reviewed posts.
    
    Useful for auditing and reviewing past decisions.
    """
    try:
        # This would need a proper query on human_decision field
        # For now, return empty list as placeholder
        return {
            "reviews": [],
            "total": 0,
            "note": "History feature requires additional implementation"
        }
        
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issue/{issue_id}")
async def get_issue_details(issue_id: str):
    """
    Get detailed information about a specific issue.
    
    Includes AI analysis results, similar cases, and any human decisions.
    """
    try:
        # Query vector service for this specific issue
        # This would need a dedicated method
        return {
            "issue_id": issue_id,
            "note": "Detailed view requires additional implementation",
            "similar_cases": [],
            "ai_analysis": {},
            "human_decision": None
        }
        
    except Exception as e:
        logger.error(f"Failed to get issue details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Webhook Management Endpoints
# ============================================================================

@router.get("/webhooks/pending")
async def get_pending_webhooks():
    """Get list of failed webhook deliveries waiting for retry."""
    return {
        "pending": WebhookService.get_pending_deliveries(),
        "count": len(WebhookService.get_pending_deliveries())
    }


@router.post("/webhooks/retry")
async def retry_pending_webhooks():
    """Retry all failed webhook deliveries."""
    results = await WebhookService.retry_pending_deliveries()
    return results
