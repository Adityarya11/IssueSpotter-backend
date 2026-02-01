from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.pipelines.moderation import ModerationPipeline
from app.services.moderation_service import ModerationService
from app.services.issue_service import IssueService
from app.services.vector_service import VectorService
from app.models.embedding import PostEmbedding
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

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
        
        # Run the AI pipeline
        pipeline_result = ModerationPipeline.process_issue(issue_data)
        
        decision = pipeline_result["results"]["decision"]
        rules = pipeline_result["results"]["rules"]
        ai = pipeline_result["results"]["ai"]
        
        # Save moderation log
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
        
        # Save embedding to Qdrant for similarity search & RAG
        if "text_embedding" in ai:
            try:
                VectorService.upsert_embedding(
                    issue_id=str(issue.id),
                    embedding=ai["text_embedding"],
                    metadata={
                        "title": issue.title,
                        "description": issue.description,
                        "ai_decision": decision["final_decision"],
                        "moderation_score": decision["moderation_score"],
                        "confidence": decision["confidence"]
                    }
                )
                logger.info(f"Stored embedding in Qdrant for issue {issue.id}")
            except Exception as e:
                logger.error(f"Failed to store embedding in Qdrant: {e}")
            
            # Also save to SQLite for backward compatibility (optional)
            embedding_record = PostEmbedding(
                issue_id=issue_uuid,
                embedding=ai["text_embedding"],
                ai_decision=decision["final_decision"]
            )
            db.add(embedding_record)
        
        # Update issue status
        ModerationService.update_issue_after_moderation(
            db=db,
            issue_id=issue_uuid,
            final_status=decision["final_status"],
            moderation_score=decision["moderation_score"]
        )
        
        db.commit()
        
        return {
            "issue_id": issue_id,
            "status": decision["final_status"],
            "decision": decision["final_decision"],
            "score": decision["moderation_score"],
            "has_nsfw": ai.get("image_analysis", {}).get("has_nsfw", False)
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e), "issue_id": issue_id}
        
    finally:
        db.close()