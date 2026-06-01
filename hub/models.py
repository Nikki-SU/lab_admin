from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum


class UserLevel(str, enum.Enum):
    ADMIN = "ADMIN"
    GROUP_ADMIN = "GROUP_ADMIN"
    MEMBER = "MEMBER"
    TRAINEE = "TRAINEE"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class DeviceType(str, enum.Enum):
    HUB = "HUB"
    LEAF = "LEAF"
    PC = "PC"


class DeviceSubtype(str, enum.Enum):
    LEAF_DATA = "LEAF_DATA"
    LEAF_PRESENT = "LEAF_PRESENT"


class DeviceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    DISABLED = "DISABLED"


class FileZone(str, enum.Enum):
    DATA = "DATA"
    COLLABORATION = "COLLABORATION"


class FileStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class SourceType(str, enum.Enum):
    LEAF_DATA = "LEAF_DATA"
    LEAF_PRESENT = "LEAF_PRESENT"
    PC = "PC"


class PermissionResource(str, enum.Enum):
    OWN_DATA = "OWN_DATA"
    OTHER_DATA = "OTHER_DATA"
    GROUP_DATA = "GROUP_DATA"
    ALL_DATA = "ALL_DATA"


class PermissionAccess(str, enum.Enum):
    READONLY = "READONLY"
    READ_DOWNLOAD = "READ_DOWNLOAD"
    READ_WRITE = "READ_WRITE"


class ShareAccess(str, enum.Enum):
    READONLY = "READONLY"
    READ_DOWNLOAD = "READ_DOWNLOAD"


class RemoteAccessPriority(str, enum.Enum):
    HIGH = "HIGH"
    LOW = "LOW"


class RemoteAccessStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    KICKED = "KICKED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class LogAction(str, enum.Enum):
    ADD = "ADD"
    DEL = "DEL"
    RENAME = "RENAME"
    MOVE = "MOVE"
    COPY = "COPY"
    EDIT = "EDIT"
    PERM = "PERM"
    SHARE = "SHARE"
    UNSHARE = "UNSHARE"
    COLLAB_ADD = "COLLAB_ADD"
    COLLAB_DOWNLOAD = "COLLAB_DOWNLOAD"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    REMOTE_REQ = "REMOTE_REQ"
    REMOTE_APPROVE = "REMOTE_APPROVE"
    REMOTE_ASSIGN = "REMOTE_ASSIGN"
    REMOTE_KICK = "REMOTE_KICK"
    REMOTE_RELEASE = "REMOTE_RELEASE"
    REMOTE_EXPIRE = "REMOTE_EXPIRE"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    level = Column(SQLEnum(UserLevel), nullable=False)
    group_id = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    granted_by = Column(String, nullable=False)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)

    devices = relationship("Device", back_populates="bound_user")
    owned_files = relationship("File", back_populates="owner")
    permissions = relationship("Permission", back_populates="target_user")
    shares_from = relationship("Share", foreign_keys="Share.from_user_id", back_populates="from_user")
    shares_to = relationship("Share", foreign_keys="Share.to_user_id", back_populates="to_user")
    remote_sessions = relationship("RemoteAccessSession", back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, index=True)
    type = Column(SQLEnum(DeviceType), nullable=False)
    subtype = Column(SQLEnum(DeviceSubtype), nullable=True)
    name = Column(String, nullable=True)
    bound_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    ip = Column(String, nullable=True)
    watch_paths = Column(JSON, nullable=True)
    registered_by = Column(String, nullable=True)
    registered_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(DeviceStatus), nullable=False, default=DeviceStatus.ACTIVE)
    registration_code = Column(String, nullable=True, unique=True)

    bound_user = relationship("User", back_populates="devices")
    uploaded_files = relationship("File", back_populates="source_device_obj")


class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, index=True)
    zone = Column(SQLEnum(FileZone), nullable=False)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    size = Column(BigInteger, nullable=False)
    hash = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    edited = Column(Boolean, nullable=False, default=False)
    edit_count = Column(Integer, nullable=False, default=0)
    original_file_id = Column(String, nullable=True)
    uploader = Column(String, nullable=False)
    upload_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    source_device = Column(String, nullable=False)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    metadata = Column(JSON, nullable=True)
    status = Column(SQLEnum(FileStatus), nullable=False, default=FileStatus.ACTIVE)

    owner = relationship("User", back_populates="owned_files")
    source_device_obj = relationship("Device", back_populates="uploaded_files")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, index=True)
    target_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    resource_type = Column(SQLEnum(PermissionResource), nullable=False)
    resource_path = Column(String, nullable=True)
    access = Column(SQLEnum(PermissionAccess), nullable=False)
    granted_by = Column(String, nullable=False)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime, nullable=True)

    target_user = relationship("User", back_populates="permissions")


class Share(Base):
    __tablename__ = "shares"

    id = Column(String, primary_key=True, index=True)
    from_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    file_ids = Column(JSON, nullable=False)
    access = Column(SQLEnum(ShareAccess), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime, nullable=True)

    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="shares_from")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="shares_to")


class RemoteAccessSession(Base):
    __tablename__ = "remote_access_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    duration_hours = Column(Integer, nullable=True)
    duration_days = Column(Integer, nullable=True)
    priority = Column(SQLEnum(RemoteAccessPriority), nullable=False)
    approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String, nullable=True)
    status = Column(SQLEnum(RemoteAccessStatus), nullable=False, default=RemoteAccessStatus.PENDING)
    granted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    kicked_by = Column(String, nullable=True)
    kicked_at = Column(DateTime, nullable=True)
    queue_position = Column(Integer, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="remote_sessions")


class Log(Base):
    __tablename__ = "logs"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    operator = Column(String, nullable=False)
    location = Column(String, nullable=False)
    action = Column(SQLEnum(LogAction), nullable=False)
    detail = Column(String, nullable=False)
