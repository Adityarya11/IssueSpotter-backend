from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID, uuid4

from app.db.session import get_db
from app.schemas.issue import IssueCreate, IssueResponse
from app.services.issue_service import IssueService
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/issues", tags=["issues"])

@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def create_issue(
    issue: IssueCreate,
    db: Session = Depends(get_db)
):
    mock_user_id = uuid4()
    
    db_issue = IssueService.create_issue(db=db, issue_data=issue, user_id=mock_user_id)
    
    celery_app.send_task("moderate_issue", args=[str(db_issue.id)])
    
    return db_issue

@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: UUID,
    db: Session = Depends(get_db)
):
    issue = IssueService.get_issue_by_id(db=db, issue_id=issue_id)
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    return issue

@router.get("/", response_model=List[IssueResponse])
async def get_issues(
    country: str,
    state: str = None,
    city: str = None,
    district: str = None,
    locality: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    issues = IssueService.get_issues_by_location(
        db=db,
        country=country,
        state=state,
        city=city,
        district=district,
        locality=locality,
        skip=skip,
        limit=limit
    )
    
    return issues