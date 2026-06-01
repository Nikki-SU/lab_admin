from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Enum as SQLEnum, Text, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

DATABASE_URL = "sqlite:///./labvault.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class UserLevel(enum.Enum):
    ADMIN = "ADMIN"  # L1
    GROUP_ADMIN = "GROUP_ADMIN"  # L2
    MEMBER = "MEMBER"  # L3
    TRAINEE = "TRAINEE"  # L4


class UserStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class DeviceType(enum.Enum):
    HUB = "HUB"
    LEAF = "LEAF"
    PC = "PC"


class DeviceSubtype(enum.Enum):
    LEAF_DATA = "LEAF_DATA"
    LEAF_PRESENT = "LEAF_PRESENT"


class DeviceStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    DISABLED = "DISABLED"


class FileZone(enum.Enum):
    DATA = "DATA"
    COLLABORATION = "COLLABORATION"


class FileStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class SourceType(enum.Enum):
    LEAF_DATA = "LEAF_DATA"
    LEAF_PRESENT = "LEAF_PRESENT"
    PC = "PC"


class PermissionResourceType(enum.Enum):
    OWN_DATA = "OWN_DATA"
    OTHER_DATA = "OTHER_DATA"
    GROUP_DATA = "GROUP_DATA"
    ALL_DATA = "ALL_DATA"


class PermissionAccess(enum.Enum):
    READONLY = "READONLY"
    READ_DOWNLOAD = "READ_DOWNLOAD"
    READ_WRITE = "READ_WRITE"


class ShareAccess(enum.Enum):
    READONLY = "READONLY"
    READ_DOWNLOAD = "READ_DOWNLOAD"


class RemoteAccessPriority(enum.Enum):
    HIGH = "HIGH"
    LOW = "LOW"


class RemoteAccessStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    KICKED = "KICKED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class LogAction(enum.Enum):
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
    hashed_password = Column(String, nullable=False)
    level = Column(SQLEnum(UserLevel), nullable=False)
    group_id = Column(String, nullable=True)
    granted_by = Column(String, nullable=False)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)


class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, index=True)
    type = Column(SQLEnum(DeviceType), nullable=False)
    subtype = Column(SQLEnum(DeviceSubtype), nullable=True)
    name = Column(String, nullable=True)
    bound_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    ip = Column(String, nullable=True)
    watch_paths = Column(Text, nullable=True)
    registered_by = Column(String, nullable=True)
    registered_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(DeviceStatus), nullable=False, default=DeviceStatus.OFFLINE)


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
    uploader = Column(String, ForeignKey("users.id"), nullable=False)
    upload_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    source_device = Column(String, nullable=False)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    metadata = Column(Text, nullable=True)  # JSON string for metadata
    status = Column(SQLEnum(FileStatus), nullable=False, default=FileStatus.ACTIVE)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, index=True)
    target_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    resource_type = Column(SQLEnum(PermissionResourceType), nullable=False)
    resource_path = Column(String, nullable=True)
    access = Column(SQLEnum(PermissionAccess), nullable=False)
    granted_by = Column(String, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime, nullable=True)


class Share(Base):
    __tablename__ = "shares"

    id = Column(String, primary_key=True, index=True)
    from_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    file_ids = Column(Text, nullable=False)  # JSON array of file IDs
    access = Column(SQLEnum(ShareAccess), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime, nullable=True)


class RemoteAccessSession(Base):
    __tablename__ = "remote_access_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    duration_hours = Column(Integer, nullable=False, default=0)
    duration_days = Column(Integer, nullable=False, default=0)
    priority = Column(SQLEnum(RemoteAccessPriority), nullable=False, default=RemoteAccessPriority.LOW)
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


class Log(Base):
    __tablename__ = "logs"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    operator = Column(String, nullable=False)
    location = Column(String, nullable=False)
    action = Column(SQLEnum(LogAction), nullable=False)
    detail = Column(Text, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)
