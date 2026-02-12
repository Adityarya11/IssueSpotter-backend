from typing import Dict
from app.utils.enums import ModerationDecision, ContentDecision

class DecisionEngine:
    """
    Decision engine for AI Guardian - Maps moderation scores to GREEN/YELLOW/RED decisions.
    """
    
    RED_THRESHOLD = 0.8    # Above = auto-reject
    YELLOW_THRESHOLD = 0.3  # Between = needs review
    # Below YELLOW_THRESHOLD = auto-approve (GREEN)
    
    @staticmethod
    def make_decision(
        rules_result: Dict,
        preprocessing_result: Dict,
        ai_result: Dict
    ) -> Dict:
        """
        Make final moderation decision based on rules and AI analysis.
        Returns GREEN/YELLOW/RED decision for AI Guardian.
        """
        
        # Immediate rejection if rules failed
        if rules_result["decision"] == "REJECT":
            return {
                "stage": "DECISION_ENGINE",
                "final_decision": ModerationDecision.REJECT.value,
                "content_decision": ContentDecision.RED.value,
                "confidence": 1.0,
                "reason": f"Failed rule checks: {', '.join(rules_result['flags'])}",
                "moderation_score": rules_result["score"]
            }
        
        # Escalate if rules suggest review needed
        if rules_result["decision"] == "ESCALATE":
            return {
                "stage": "DECISION_ENGINE",
                "final_decision": ModerationDecision.ESCALATE.value,
                "content_decision": ContentDecision.YELLOW.value,
                "confidence": 0.7,
                "reason": "Requires human review",
                "moderation_score": rules_result["score"]
            }
        
        # Calculate combined score from AI analysis
        combined_score = (
            rules_result["score"] * 0.5 +
            ai_result.get("toxicity", 0) * 0.3 +
            (1 - ai_result.get("civic_relevance", 0.5)) * 0.2
        )
        
        # Map to three-tier decision system (GREEN/YELLOW/RED)
        if combined_score > DecisionEngine.RED_THRESHOLD:
            final_decision = ModerationDecision.REJECT.value
            content_decision = ContentDecision.RED.value
            reason = "High risk score - auto-reject"
        elif combined_score > DecisionEngine.YELLOW_THRESHOLD:
            final_decision = ModerationDecision.ESCALATE.value
            content_decision = ContentDecision.YELLOW.value
            reason = "Medium risk - needs review"
        else:
            final_decision = ModerationDecision.APPROVE.value
            content_decision = ContentDecision.GREEN.value
            reason = "Passed all checks - auto-approve"
        
        return {
            "stage": "DECISION_ENGINE",
            "final_decision": final_decision,
            "content_decision": content_decision,
            "confidence": ai_result.get("confidence", 0.5),
            "reason": reason,
            "moderation_score": combined_score
        }