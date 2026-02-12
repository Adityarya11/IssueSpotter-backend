from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ModerationService:
    """
    Moderation service for AI Guardian.
    
    NOTE: This is a simplified version without database persistence.
    For production, integrate with main backend via webhooks.
    """
    
    @staticmethod
    def log_moderation(
        issue_id: str,
        stage: str,
        decision: str,
        score: float,
        confidence: float,
        flags: list,
        reason: str,
        metadata: dict
    ) -> Dict:
        """Log moderation decision (in-memory for now, send via webhook in production)."""
        log_entry = {
            "issue_id": issue_id,
            "stage": stage,
            "decision": decision,
            "score": score,
            "confidence": confidence,
            "flags": flags,
            "metadata": metadata,
            "reason": reason
        }
        
        logger.info(f"Moderation logged for {issue_id}: {decision} (score: {score:.3f})")
        return log_entry
    
    @staticmethod
    def create_moderation_response(
        issue_id: str,
        final_decision: str,
        content_decision: str,
        moderation_score: float,
        confidence: float,
        reason: str
    ) -> Dict:
        """Create standardized moderation response for API."""
        return {
            "issue_id": issue_id,
            "decision": final_decision,
            "content_decision": content_decision,  # GREEN/YELLOW/RED
            "score": moderation_score,
            "confidence": confidence,
            "reason": reason
        }