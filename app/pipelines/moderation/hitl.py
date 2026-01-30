from typing import Dict
from app.utils.enums import IssueStatus

class HITLHandler:

    @staticmethod
    def should_escalate(desision_result: Dict) -> bool:
        return desision_result["final_status"] == IssueStatus.UNDER_REVIEW.value
    
    @staticmethod
    def create_review_task(issue_id: str, dcision_result: Dict) -> Dict:
        return {
            "issue_id": issue_id,
            "priority": "HIGH" if dcision_result["moderation_score"] > 0.7 else "NORMAL",
            "reason": dcision_result["reason"],
            "flags": dcision_result.get("flags", []),
            "confidence": dcision_result["confidence"]
        }