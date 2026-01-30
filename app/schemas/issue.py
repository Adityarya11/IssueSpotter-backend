from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID
import json

from app.utils.enums import IssueStatus, IssueCategory

# Shared properties
class IssueBase(BaseModel):
    title: str
    description: str
    category: IssueCategory = IssueCategory.OTHER
    
    country: str
    state: str
    city: str
    district: Optional[str] = None
    locality: Optional[str] = None
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    images: List[str] = []

# Properties to receive on item creation
class IssueCreate(IssueBase):
    pass

# Properties to return to client
class IssueResponse(IssueBase):
    id: UUID
    user_id: UUID
    status: IssueStatus
    moderation_score: float
    
    upvotes: int
    downvotes: int
    comment_count: int
    
    # ✅ FIX: Map the JSON 'metadata' field to the Python 'metadata_' attribute
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    # Validator to handle SQLite JSON string format
    @field_validator("images", mode="before")
    @classmethod
    def parse_images(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v