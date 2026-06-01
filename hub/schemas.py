from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .models import UserLevel, UserStatus, DeviceType, DeviceSubtype, DeviceStatus, \
    FileZone, FileStatus, SourceType, PermissionResource, PermissionAccess, \
    ShareAccess, RemoteAccessPriority, RemoteAccessStatus, LogAction


class UserBase(BaseModel):
    id: str
    name: str
    level: UserLevel
    group_id: Optional[str] = None
    granted_by: str
    granted_at: datetime
    expires_at: datetime
    status: UserStatus


class UserCreate(BaseModel):
    id: str
    name: str
    password: str
    level: UserLevel
    group_id: Optional[str] = None
    expires_at: datetime


class UserLogin(BaseModel):
    user_id: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class DeviceBase(BaseModel):
    id: str
    type: DeviceType
    subtype: Optional[DeviceSubtype] = None
    name: Optional[str] = None
    bound_user_id: Optional[str] = None
    ip: Optional[str] = None
    watch_paths: Optional[List[str]] = None
    status: DeviceStatus


class DeviceCreate(BaseModel):
    name: str
    subtype: DeviceSubtype = DeviceSubtype.LEAF_DATA
    ip: Optional[str] = None
    watch_paths: Optional[List[str]] = None


class FileBase(BaseModel):
    id: str
    zone: FileZone
    name: str
    path: str
    size: int
    hash: str
    owner_id: str
    edited: bool
    edit_count: int
    original_file_id: Optional[str] = None
    uploader: str
    upload_time: datetime
    source_device: str
    source_type: SourceType
    metadata: Optional[dict] = None
    status: FileStatus


class FileMetadata(BaseModel):
    date: Optional[str] = None
    operator: Optional[str] = None
    sample: Optional[str] = None
    experiment_type: Optional[str] = None
    experiment_subtype: Optional[str] = None
    device: Optional[str] = None


class FileUpload(BaseModel):
    name: str
    zone: FileZone
    metadata: Optional[FileMetadata] = None


class FileListResponse(BaseModel):
    files: List[FileBase]
    total: int


class PermissionBase(BaseModel):
    id: str
    target_user_id: str
    resource_type: PermissionResource
    resource_path: Optional[str] = None
    access: PermissionAccess
    granted_by: str
    granted_at: datetime
    expires_at: datetime
    revoked: bool
    revoked_at: Optional[datetime] = None


class ShareBase(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    file_ids: List[str]
    access: ShareAccess
    created_at: datetime
    expires_at: datetime
    revoked: bool
    revoked_at: Optional[datetime] = None


class ShareCreate(BaseModel):
    to_user_id: str
    file_ids: List[str]
    access: ShareAccess
    expires_at: datetime


class LogBase(BaseModel):
    id: str
    timestamp: datetime
    operator: str
    location: str
    action: LogAction
    detail: str


class LogQuery(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    operator: Optional[str] = None
    action: Optional[LogAction] = None
    location: Optional[str] = None


class Message(BaseModel):
    message: str
