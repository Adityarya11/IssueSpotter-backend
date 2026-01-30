from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Uuid, JSON
from sqlalchemy.sql import func
import uuid
from app.db.session import Base
from app.utils.enums import ModerationStage, ModerationDecision

class ModerationLog(Base):
    __tablename__ = "moderation_logs"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(Uuid(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    
    stage = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    
    score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    
    # Use generic JSON
    flags = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)
    
    reason = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())