from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.utils.enums import IssueStatus, IssueCategory

class IssueBase(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    description: str = Field(..., min_length=20)
    category: IssueCategory = IssueCategory.OTHER
    
    country: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    locality: Optional[str] = Field(None, max_length=100)
    
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    images: List[str] = Field(default_factory=list)

    @field_validator('title', 'description')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

class IssueCreate(IssueBase):
    pass

class IssueResponse(IssueBase):
    id: str
    user_id: str
    status: IssueStatus
    moderation_score: float
    upvotes: int
    downvotes: int
    comment_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True