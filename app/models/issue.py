from sqlalchemy import Column, String, Text, DateTime, Float, Integer, ForeignKey, Uuid, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.utils.enums import IssueStatus, IssueCategory

class Issue(Base):
    """
    Temporary storage for posts being moderated.
    
    NOTE: This is NOT the main issue database.
    Main backend stores the canonical post data.
    This model exists only for:
    1. Holding post data during AI processing
    2. Linking to moderation logs
    3. Storing embeddings for similarity search
    """
    __tablename__ = "issues"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), nullable=False)  # From main backend
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    images = Column(JSON, default=list)
    category = Column(String, default=IssueCategory.OTHER.value)
    
    # Geographic data (for context-aware moderation)
    country = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100))
    locality = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Moderation state
    status = Column(String, default=IssueStatus.PENDING.value, index=True)
    moderation_score = Column(Float, default=0.0)
    
    # AI-specific fields
    text_embedding = Column(JSON)  # Store the 384-dim vector
    
    # Metrics (for internal tracking)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    metadata_ = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # No relationship to User model (we don't manage users)