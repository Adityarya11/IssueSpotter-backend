from sqlalchemy import Column, String, Text, DateTime, Float, Integer, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.utils.enums import IssueStatus, IssueCategory

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    images = Column(ARRAY(String), default=[])
    
    category = Column(String, default=IssueCategory.OTHER.value)
    
    country = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100))
    locality = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    
    status = Column(String, default=IssueStatus.PENDING.value, index=True)
    moderation_score = Column(Float, default=0.0)
    
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="issues")