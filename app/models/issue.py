from sqlalchemy import Column, String, Text, DateTime, Float, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.utils.enums import IssueStatus, IssueCategory
from app.models.types import JSONEncodedType

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    images = Column(JSONEncodedType, default=list)
    
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
    
    extra_data = Column(JSONEncodedType, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="issues")