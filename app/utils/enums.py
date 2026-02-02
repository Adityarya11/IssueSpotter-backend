from enum import Enum

class ModerationStage(str, Enum):
    """Stages in the moderation pipeline"""
    RULES = "RULES"
    PREPROCESSING = "PREPROCESSING"
    AI_CLASSIFIER = "AI_CLASSIFIER"
    DECISION_ENGINE = "DECISION_ENGINE"
    HITL = "HITL"

class ModerationDecision(str, Enum):
    """Final moderation decisions"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"
    SHADOW_BAN = "SHADOW_BAN"

class ContentDecision(str, Enum):
    """Three-tier AI decision system"""
    GREEN = "GREEN"      # Auto-approve
    YELLOW = "YELLOW"    # Human review needed
    RED = "RED"          # Auto-reject