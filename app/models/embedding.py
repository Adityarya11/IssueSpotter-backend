from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, JSON
from sqlalchemy.sql import func
import uuid
from app.db.session import Base

class PostEmbedding(Base):
    """
    Store text embeddings for semantic similarity search.
    Used for duplicate detection and continuous learning.
    """
    __tablename__ = "post_embeddings"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(Uuid(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    
    # The 384-dimensional vector (stored as JSON array)
    embedding = Column(JSON, nullable=False)
    
    # Moderation outcome (for learning)
    human_decision = Column(String)  # What moderator said
    ai_decision = Column(String)      # What AI predicted
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())