from sqlalchemy.orm import Session
from app.models.moderation import ModerationLog
from app.models.issue import Issue
from app.utils.enums import IssueStatus
from uuid import UUID

class ModerationService:
    
    @staticmethod
    def log_moderation(
        db: Session,
        issue_id: str,
        stage: str,
        decision: str,
        score: float,
        confidence: float,
        flags: list,
        reason: str,
        metadata: dict
    ) -> ModerationLog:
        log = ModerationLog(
            issue_id=UUID(issue_id),
            stage=stage,
            decision=decision,
            score=score,
            confidence=confidence,
            flags=flags,
            metadata_=metadata,
            reason=reason
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        return log
    
    @staticmethod
    def update_issue_after_moderation(
        db: Session,
        issue_id: UUID,
        final_status: str,
        moderation_score: float
    ) -> Issue:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        
        if not issue:
            return None
        
        issue.status = final_status
        issue.moderation_score = moderation_score
        
        db.commit()
        db.refresh(issue)
        
        return issue