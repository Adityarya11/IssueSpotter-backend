from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer
from sqlalchemy.sql import func
import uuid
from app.db.session import Base
from app.utils.enums import UserRole

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    role = Column(String, default=UserRole.USER.value)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    trust_score = Column(Float, default=0.5)
    total_posts = Column(Integer, default=0)
    approved_posts = Column(Integer, default=0)
    flagged_posts = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())