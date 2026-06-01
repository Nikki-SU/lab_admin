from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from datetime import datetime

from ..database import get_db
from ..models import User, UserLevel, UserStatus, LogAction
from ..schemas import UserLogin, Token, Message
from ..auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from ..config import settings
from ..utils import generate_uuid
from ..logging_service import log_action

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    log_action(db, user.id, "SERVER", LogAction.LOGIN, "PC")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register/init", response_model=Message)
async def initialize_system(db: Session = Depends(get_db)):
    existing_admin = db.query(User).filter(User.level == UserLevel.ADMIN).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System already initialized"
        )
    
    hashed_password = get_password_hash("admin123")
    admin_user = User(
        id="admin",
        name="System Administrator",
        level=UserLevel.ADMIN,
        hashed_password=hashed_password,
        granted_by="system",
        granted_at=datetime.utcnow(),
        expires_at=datetime(2999, 12, 31),
        status=UserStatus.ACTIVE
    )
    db.add(admin_user)
    db.commit()
    
    return {"message": "System initialized. Admin user: admin / admin123. Please change password immediately!"}


@router.post("/logout", response_model=Message)
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_action(db, current_user.id, "SERVER", LogAction.LOGOUT, "PC")
    return {"message": "Logged out successfully"}
