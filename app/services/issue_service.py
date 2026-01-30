from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.issue import Issue
from app.schemas.issue import IssueCreate
from app.utils.enums import IssueStatus
import json

class IssueService:
    
    @staticmethod
    def create_issue(db: Session, issue_data: IssueCreate, user_id: str) -> Issue:
        db_issue = Issue(
            user_id=user_id,
            title=issue_data.title,
            description=issue_data.description,
            images=json.dumps(issue_data.images),
            category=issue_data.category.value,
            country=issue_data.country,
            state=issue_data.state,
            city=issue_data.city,
            district=issue_data.district,
            locality=issue_data.locality,
            latitude=issue_data.latitude,
            longitude=issue_data.longitude,
            status=IssueStatus.PENDING.value
        )
        
        db.add(db_issue)
        db.commit()
        db.refresh(db_issue)
        
        return db_issue
    
    @staticmethod
    def get_issue_by_id(db: Session, issue_id: str) -> Optional[Issue]:
        return db.query(Issue).filter(Issue.id == issue_id).first()
    
    @staticmethod
    def get_issues_by_location(
        db: Session,
        country: str,
        state: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        locality: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Issue]:
        query = db.query(Issue).filter(
            Issue.status == IssueStatus.APPROVED.value,
            Issue.country == country
        )
        
        if state:
            query = query.filter(Issue.state == state)
        if city:
            query = query.filter(Issue.city == city)
        if district:
            query = query.filter(Issue.district == district)
        if locality:
            query = query.filter(Issue.locality == locality)
        
        return query.order_by(Issue.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_issue_status(
        db: Session,
        issue_id: str,
        status: IssueStatus,
        moderation_score: Optional[float] = None
    ) -> Optional[Issue]:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return None
        
        issue.status = status.value
        if moderation_score is not None:
            issue.moderation_score = moderation_score
        
        db.commit()
        db.refresh(issue)
        
        return issue