from typing import Dict
from app.utils.enums import ModerationDecision, IssueStatus

class DecisionEngine:
    
    REJECT_THRESHOLD = 0.8
    ESCALATE_THRESHOLD = 0.5
    
    @staticmethod
    def make_decision(
        rules_result: Dict,
        preprocessing_result: Dict,
        ai_result: Dict
    ) -> Dict:
        
        if rules_result["decision"] == "REJECT":
            return {
                "stage": "DECISION_ENGINE",
                "final_decision": ModerationDecision.REJECT.value,
                "final_status": IssueStatus.REJECTED.value,
                "confidence": 1.0,
                "reason": f"Failed rule checks: {', '.join(rules_result['flags'])}",
                "moderation_score": rules_result["score"]
            }
        
        if rules_result["decision"] == "ESCALATE":
            return {
                "stage": "DECISION_ENGINE",
                "final_decision": ModerationDecision.ESCALATE.value,
                "final_status": IssueStatus.UNDER_REVIEW.value,
                "confidence": 0.7,
                "reason": "Requires human review",
                "moderation_score": rules_result["score"]
            }
        
        combined_score = (
            rules_result["score"] * 0.5 +
            ai_result.get("toxicity", 0) * 0.3 +
            (1 - ai_result.get("civic_relevance", 0.5)) * 0.2
        )
        
        if combined_score > DecisionEngine.REJECT_THRESHOLD:
            final_decision = ModerationDecision.REJECT.value
            final_status = IssueStatus.REJECTED.value
            reason = "High risk score"
        elif combined_score > DecisionEngine.ESCALATE_THRESHOLD:
            final_decision = ModerationDecision.ESCALATE.value
            final_status = IssueStatus.UNDER_REVIEW.value
            reason = "Medium risk - needs review"
        else:
            final_decision = ModerationDecision.APPROVE.value
            final_status = IssueStatus.APPROVED.value
            reason = "Passed all checks"
        
        return {
            "stage": "DECISION_ENGINE",
            "final_decision": final_decision,
            "final_status": final_status,
            "confidence": ai_result.get("confidence", 0.5),
            "reason": reason,
            "moderation_score": combined_score
        }