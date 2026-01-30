from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.pipelines.moderation import ModerationPipeline
from app.services.moderation_service import ModerationService
from app.services.issue_service import IssueService
from uuid import UUID

@celery_app.task(name="moderate_issue")
def moderate_issue_task(issue_id: str):
    db = SessionLocal()
    
    try:
        issue_uuid = UUID(issue_id)
        issue = IssueService.get_issue_by_id(db, issue_uuid)
        
        if not issue:
            return {"error": "Issue not found", "issue_id": issue_id}
        
        issue_data = {
            "id": str(issue.id),
            "title": issue.title,
            "description": issue.description,
            "images": issue.images if isinstance(issue.images, list) else []
        }
        
        pipeline_result = ModerationPipeline.process_issue(issue_data)
        
        decision = pipeline_result["results"]["decision"]
        rules = pipeline_result["results"]["rules"]
        
        ModerationService.log_moderation(
            db=db,
            issue_id=str(issue.id),
            stage=decision["stage"],
            decision=decision["final_decision"],
            score=decision["moderation_score"],
            confidence=decision["confidence"],
            flags=rules.get("flags", []),
            reason=decision["reason"],
            metadata=pipeline_result["results"]
        )
        
        ModerationService.update_issue_after_moderation(
            db=db,
            issue_id=issue_uuid,
            final_status=decision["final_status"],
            moderation_score=decision["moderation_score"]
        )
        
        return {
            "issue_id": issue_id,
            "status": decision["final_status"],
            "decision": decision["final_decision"],
            "score": decision["moderation_score"]
        }
        
    except Exception as e:
        return {"error": str(e), "issue_id": issue_id}
        
    finally:
        db.close()