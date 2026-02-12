from typing import Dict
from app.utils.enums import ContentDecision, ModerationDecision

class HITLHandler:
    """Human-in-the-Loop handler for AI Guardian - manages YELLOW flag escalations."""

    @staticmethod
    def should_escalate(decision_result: Dict) -> bool:
        """Check if content needs human review (YELLOW decision)."""
        content_decision = decision_result.get("content_decision")
        final_decision = decision_result.get("final_decision")
        
        # Escalate if YELLOW or explicit ESCALATE decision
        return (content_decision == ContentDecision.YELLOW.value or 
                final_decision == ModerationDecision.ESCALATE.value)
    
    @staticmethod
    def create_review_task(issue_id: str, decision_result: Dict) -> Dict:
        """Create a task for human reviewers in the dashboard."""
        return {
            "issue_id": issue_id,
            "priority": "HIGH" if decision_result["moderation_score"] > 0.7 else "NORMAL",
            "reason": decision_result["reason"],
            "flags": decision_result.get("flags", []),
            "confidence": decision_result["confidence"],
            "content_decision": decision_result.get("content_decision", "YELLOW")
        }