from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..models import User, UserLevel, UserStatus, LogAction
from ..schemas import UserBase, UserCreate, Message
from ..auth import get_current_user, get_password_hash, check_user_permission
from ..utils import generate_uuid
from ..logging_service import log_action

router = APIRouter()


@router.get("/me", response_model=UserBase)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=List[UserBase])
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.level == UserLevel.ADMIN:
        users = db.query(User).all()
    elif current_user.level == UserLevel.GROUP_ADMIN:
        users = db.query(User).filter(
            (User.group_id == current_user.group_id) | (User.id == current_user.id)
        ).all()
    else:
        users = [current_user]
    return users


@router.post("/", response_model=UserBase)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if db.query(User).filter(User.id == user.id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID already exists"
        )
    
    if current_user.level == UserLevel.MEMBER or current_user.level == UserLevel.TRAINEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if user.level == UserLevel.ADMIN and current_user.level != UserLevel.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create admin users"
        )
    
    if user.level in [UserLevel.GROUP_ADMIN, UserLevel.MEMBER, UserLevel.TRAINEE]:
        if current_user.level == UserLevel.GROUP_ADMIN:
            if not user.group_id or user.group_id != current_user.group_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Group admin can only create users in their own group"
                )
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        id=user.id,
        name=user.name,
        level=user.level,
        group_id=user.group_id,
        hashed_password=hashed_password,
        granted_by=current_user.id,
        granted_at=datetime.utcnow(),
        expires_at=user.expires_at,
        status=UserStatus.ACTIVE
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_action(
        db, current_user.id, "SERVER", LogAction.PERM,
        f"Created user {user.id} with level {user.level}"
    )
    
    return new_user


@router.put("/{user_id}/status", response_model=Message)
async def update_user_status(
    user_id: str,
    new_status: UserStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if current_user.level == UserLevel.ADMIN:
        pass
    elif current_user.level == UserLevel.GROUP_ADMIN:
        if user.group_id != current_user.group_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user.status = new_status
    db.commit()
    
    log_action(
        db, current_user.id, "SERVER", LogAction.PERM,
        f"Changed user {user_id} status to {new_status}"
    )
    
    return {"message": f"User status updated to {new_status}"}
