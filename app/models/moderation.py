from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
import uuid
from app.db.session import Base
from app.utils.enums import ModerationStage, ModerationDecision
from app.models.types import JSONEncodedType

class ModerationLog(Base):
    __tablename__ = "moderation_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = Column(String(36), ForeignKey("issues.id"), nullable=False)
    
    stage = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    
    score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    
    flags = Column(JSONEncodedType, default=list)
    extra_data = Column(JSONEncodedType, default=dict)
    
    reason = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())