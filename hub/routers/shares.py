from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import User, UserLevel, Share, ShareAccess, LogAction
from ..schemas import ShareBase, ShareCreate, Message
from ..auth import get_current_user
from ..utils import generate_uuid
from ..logging_service import log_action

router = APIRouter()


@router.get("/received", response_model=List[ShareBase])
async def get_received_shares(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shares = db.query(Share).filter(
        Share.to_user_id == current_user.id,
        Share.revoked == False,
        Share.expires_at > datetime.utcnow()
    ).all()
    return shares


@router.get("/sent", response_model=List[ShareBase])
async def get_sent_shares(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shares = db.query(Share).filter(Share.from_user_id == current_user.id).all()
    return shares


@router.post("/", response_model=ShareBase)
async def create_share(
    share: ShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user = db.query(User).filter(User.id == share.to_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    new_share = Share(
        id=generate_uuid(),
        from_user_id=current_user.id,
        to_user_id=share.to_user_id,
        file_ids=share.file_ids,
        access=share.access,
        created_at=datetime.utcnow(),
        expires_at=share.expires_at,
        revoked=False
    )
    
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    
    log_action(
        db, current_user.id, "SERVER", LogAction.SHARE,
        f"→{share.to_user_id}:{share.access}:{','.join(share.file_ids[:3])}"
    )
    
    return new_share


@router.post("/{share_id}/revoke", response_model=Message)
async def revoke_share(
    share_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    share = db.query(Share).filter(Share.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    if share.from_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    share.revoked = True
    share.revoked_at = datetime.utcnow()
    db.commit()
    
    log_action(
        db, current_user.id, "SERVER", LogAction.UNSHARE,
        f"←{share.to_user_id}:{','.join(share.file_ids[:3])}"
    )
    
    return {"message": "Share revoked successfully"}
