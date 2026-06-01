from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, UserLevel, Log, LogAction
from ..schemas import LogBase, LogQuery
from ..auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[LogBase])
async def get_logs(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    operator: Optional[str] = None,
    action: Optional[LogAction] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Log)
    
    if current_user.level == UserLevel.MEMBER or current_user.level == UserLevel.TRAINEE:
        query = query.filter(Log.operator == current_user.id)
    elif current_user.level == UserLevel.GROUP_ADMIN:
        from ..models import User
        group_users = db.query(User).filter(User.group_id == current_user.group_id).all()
        group_user_ids = [u.id for u in group_users]
        group_user_ids.append(current_user.id)
        query = query.filter(Log.operator.in_(group_user_ids))
    
    if start_time:
        query = query.filter(Log.timestamp >= start_time)
    if end_time:
        query = query.filter(Log.timestamp <= end_time)
    if operator:
        query = query.filter(Log.operator == operator)
    if action:
        query = query.filter(Log.action == action)
    if location:
        query = query.filter(Log.location == location)
    
    logs = query.order_by(Log.timestamp.desc()).limit(1000).all()
    
    return logs


@router.get("/my", response_model=List[LogBase])
async def get_my_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logs = db.query(Log).filter(Log.operator == current_user.id).order_by(
        Log.timestamp.desc()
    ).limit(100).all()
    return logs
