from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import User, UserLevel, Device, DeviceType, DeviceSubtype, DeviceStatus, LogAction
from ..schemas import DeviceBase, DeviceCreate, Message
from ..auth import get_current_user
from ..utils import generate_uuid, generate_registration_code
from ..logging_service import log_action

router = APIRouter()


@router.get("/", response_model=List[DeviceBase])
async def get_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.level == UserLevel.ADMIN:
        devices = db.query(Device).all()
    elif current_user.level == UserLevel.GROUP_ADMIN:
        devices = db.query(Device).filter(
            (Device.bound_user_id == current_user.id) |
            (Device.registered_by == current_user.id)
        ).all()
    else:
        devices = db.query(Device).filter(Device.bound_user_id == current_user.id).all()
    return devices


@router.post("/", response_model=DeviceBase)
async def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.level == UserLevel.MEMBER or current_user.level == UserLevel.TRAINEE:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    registration_code = generate_registration_code()
    
    new_device = Device(
        id=generate_uuid(),
        type=DeviceType.LEAF,
        subtype=device.subtype,
        name=device.name,
        ip=device.ip,
        watch_paths=device.watch_paths,
        registered_by=current_user.id,
        registered_at=datetime.utcnow(),
        status=DeviceStatus.ACTIVE,
        registration_code=registration_code
    )
    
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    log_action(
        db, current_user.id, "SERVER", LogAction.ADD,
        f"Created device {device.name}"
    )
    
    return new_device


@router.post("/register/pc", response_model=DeviceBase)
async def register_pc_device(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_device = Device(
        id=generate_uuid(),
        type=DeviceType.PC,
        name=f"PC-{current_user.id}-{datetime.utcnow().strftime('%Y%m%d')}",
        bound_user_id=current_user.id,
        registered_by=current_user.id,
        registered_at=datetime.utcnow(),
        status=DeviceStatus.ACTIVE
    )
    
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    return new_device


@router.post("/leaf/register/{code}", response_model=DeviceBase)
async def register_leaf_device_by_code(
    code: str,
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.registration_code == code).first()
    if not device:
        raise HTTPException(status_code=404, detail="Invalid registration code")
    
    device.registration_code = None
    device.status = DeviceStatus.ACTIVE
    db.commit()
    db.refresh(device)
    
    return device


@router.get("/leaf/registration/{device_id}", response_model=Message)
async def get_registration_code(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if current_user.level != UserLevel.ADMIN and \
       current_user.level != UserLevel.GROUP_ADMIN and \
       device.registered_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if not device.registration_code:
        device.registration_code = generate_registration_code()
        db.commit()
    
    return {"message": device.registration_code}
