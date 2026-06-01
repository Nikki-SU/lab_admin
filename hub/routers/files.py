from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from ..database import get_db
from ..models import User, UserLevel, File, FileZone, FileStatus, SourceType, Device, DeviceSubtype, LogAction
from ..schemas import FileBase, FileListResponse, Message
from ..auth import get_current_user
from ..utils import generate_uuid, compute_file_hash, validate_data_filename, get_storage_path
from ..logging_service import log_action
from ..config import settings

router = APIRouter()


@router.post("/upload/data", response_model=FileBase)
async def upload_data_file(
    file: UploadFile = File(...),
    device_id: str = "",
    operator_id: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = None
    experiment_type = None
    
    if device_id:
        device = db.query(Device).filter(Device.id == device_id).first()
        if device:
            experiment_type = device.name
    
    valid, error = validate_data_filename(file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    if not operator_id:
        operator_id = current_user.id
    
    if not experiment_type:
        experiment_type = "unknown"
    
    temp_path = os.path.join("/tmp", f"{generate_uuid()}_{file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_hash = compute_file_hash(temp_path)
    file_size = os.path.getsize(temp_path)
    
    storage_dir = get_storage_path(FileZone.DATA, file.filename, operator_id, experiment_type)
    final_path = os.path.join(storage_dir, file.filename)
    shutil.move(temp_path, final_path)
    
    new_file = File(
        id=generate_uuid(),
        zone=FileZone.DATA,
        name=file.filename,
        path=final_path,
        size=file_size,
        hash=file_hash,
        owner_id=operator_id,
        edited=False,
        edit_count=0,
        uploader=current_user.id,
        upload_time=datetime.utcnow(),
        source_device=device_id if device_id else "PC",
        source_type=SourceType.LEAF_DATA if device else SourceType.PC,
        metadata={
            "date": datetime.utcnow().strftime("%Y%m%d"),
            "operator": operator_id,
            "sample": file.filename.split("_")[2].split(".")[0],
            "experiment_type": experiment_type,
            "device": device_id if device_id else "PC"
        },
        status=FileStatus.ACTIVE
    )
    
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    
    log_action(
        db, current_user.id, device_id if device_id else "PC",
        LogAction.ADD, file.filename
    )
    
    return new_file


@router.post("/upload/collab", response_model=FileBase)
async def upload_collab_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.level == UserLevel.TRAINEE:
        raise HTTPException(status_code=403, detail="Trainees cannot upload to collaboration zone")
    
    temp_path = os.path.join("/tmp", f"{generate_uuid()}_{file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_hash = compute_file_hash(temp_path)
    file_size = os.path.getsize(temp_path)
    
    storage_dir = get_storage_path(FileZone.COLLABORATION, file.filename, current_user.id)
    final_path = os.path.join(storage_dir, file.filename)
    shutil.move(temp_path, final_path)
    
    new_file = File(
        id=generate_uuid(),
        zone=FileZone.COLLABORATION,
        name=file.filename,
        path=final_path,
        size=file_size,
        hash=file_hash,
        owner_id=current_user.id,
        edited=False,
        edit_count=0,
        uploader=current_user.id,
        upload_time=datetime.utcnow(),
        source_device="PC",
        source_type=SourceType.PC,
        status=FileStatus.ACTIVE
    )
    
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    
    log_action(
        db, current_user.id, "PC",
        LogAction.COLLAB_ADD, f"{current_user.id}:{file.filename}"
    )
    
    return new_file


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.zone == FileZone.DATA:
        if current_user.level != UserLevel.ADMIN and \
           current_user.level != UserLevel.GROUP_ADMIN and \
           file.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if not os.path.exists(file.path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    if file.zone == FileZone.COLLABORATION:
        log_action(
            db, current_user.id, "PC",
            LogAction.COLLAB_DOWNLOAD, f"{current_user.id}:{file.name}"
        )
    
    return FileResponse(file.path, filename=file.name)


@router.get("/data", response_model=FileListResponse)
async def list_data_files(
    mode: str = "person",
    user_id: Optional[str] = None,
    experiment_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(File).filter(
        File.zone == FileZone.DATA,
        File.status == FileStatus.ACTIVE
    )
    
    if current_user.level == UserLevel.MEMBER or current_user.level == UserLevel.TRAINEE:
        query = query.filter(File.owner_id == current_user.id)
    elif current_user.level == UserLevel.GROUP_ADMIN:
        group_users = db.query(User).filter(User.group_id == current_user.group_id).all()
        group_user_ids = [u.id for u in group_users]
        query = query.filter(File.owner_id.in_(group_user_ids))
    
    files = query.order_by(File.upload_time.desc()).all()
    
    log_action(db, current_user.id, "PC", LogAction.ADD, "Listed data files")
    
    return {
        "files": files,
        "total": len(files)
    }


@router.get("/collab", response_model=FileListResponse)
async def list_collab_files(
    mode: str = "date",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(File).filter(
        File.zone == FileZone.COLLABORATION,
        File.status == FileStatus.ACTIVE
    )
    
    if current_user.level == UserLevel.GROUP_ADMIN or current_user.level == UserLevel.ADMIN:
        if current_user.group_id:
            group_users = db.query(User).filter(User.group_id == current_user.group_id).all()
            group_user_ids = [u.id for u in group_users]
            query = query.filter(File.owner_id.in_(group_user_ids))
    elif current_user.level == UserLevel.MEMBER or current_user.level == UserLevel.TRAINEE:
        if current_user.group_id:
            group_users = db.query(User).filter(User.group_id == current_user.group_id).all()
            group_user_ids = [u.id for u in group_users]
            query = query.filter(File.owner_id.in_(group_user_ids))
    
    files = query.order_by(File.upload_time.desc()).all()
    
    return {
        "files": files,
        "total": len(files)
    }


@router.get("/edited", response_model=FileListResponse)
async def list_edited_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(File).filter(
        File.zone == FileZone.DATA,
        File.edited == True,
        File.status == FileStatus.ACTIVE
    )
    
    if current_user.level == UserLevel.MEMBER or current_user.level == UserLevel.TRAINEE:
        query = query.filter(File.owner_id == current_user.id)
    elif current_user.level == UserLevel.GROUP_ADMIN:
        group_users = db.query(User).filter(User.group_id == current_user.group_id).all()
        group_user_ids = [u.id for u in group_users]
        query = query.filter(File.owner_id.in_(group_user_ids))
    
    files = query.order_by(File.upload_time.desc()).all()
    
    return {
        "files": files,
        "total": len(files)
    }


@router.post("/{file_id}/edit", response_model=FileBase)
async def mark_file_edited(
    file_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    original_file = db.query(File).filter(File.id == file_id).first()
    if not original_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if original_file.owner_id != current_user.id and \
       current_user.level != UserLevel.ADMIN and \
       current_user.level != UserLevel.GROUP_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    temp_path = os.path.join("/tmp", f"{generate_uuid()}_{file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_hash = compute_file_hash(temp_path)
    file_size = os.path.getsize(temp_path)
    
    storage_dir = os.path.dirname(original_file.path)
    final_path = os.path.join(storage_dir, file.filename)
    shutil.move(temp_path, final_path)
    
    new_file = File(
        id=generate_uuid(),
        zone=original_file.zone,
        name=file.filename,
        path=final_path,
        size=file_size,
        hash=file_hash,
        owner_id=original_file.owner_id,
        edited=True,
        edit_count=original_file.edit_count + 1,
        original_file_id=original_file.id,
        uploader=current_user.id,
        upload_time=datetime.utcnow(),
        source_device="PC",
        source_type=SourceType.PC,
        metadata=original_file.metadata,
        status=FileStatus.ACTIVE
    )
    
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    
    log_action(
        db, current_user.id, "PC",
        LogAction.EDIT, file.filename
    )
    
    return new_file
