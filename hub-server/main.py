from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
import os
import uuid
import hashlib
from dotenv import load_dotenv
from database import (
    SessionLocal, init_db, User, UserLevel, File, FileZone, FileStatus,
    Device, DeviceType, DeviceStatus, Log, LogAction, Share, ShareAccess,
    SourceType
)

# Load environment variables
load_dotenv()

app = FastAPI(title="LabVault Hub Server")

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


init_db()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    id: str
    name: str
    password: str
    level: UserLevel
    group_id: Optional[str] = None
    expires_in_days: int = 365


class UserResponse(BaseModel):
    id: str
    name: str
    level: UserLevel
    group_id: Optional[str] = None
    status: str


class FileResponse(BaseModel):
    id: str
    zone: str
    name: str
    path: str
    size: int
    owner_id: str
    edited: bool
    edit_count: int
    uploader: str
    upload_time: datetime
    source_type: str
    metadata: Optional[Dict] = None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, user_id: str, password: str):
    user = get_user(db, user_id)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, user_id=token_data.username)
    if user is None:
        raise credentials_exception
    if user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="User account is not active")
    return user


def log_action(db: Session, operator: str, location: str, action: LogAction, detail: str):
    log_entry = Log(
        id=str(uuid.uuid4()),
        operator=operator,
        location=location,
        action=action,
        detail=detail
    )
    db.add(log_entry)
    db.commit()


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin = db.query(User).filter(User.id == "admin").first()
        if not admin:
            # Create default admin user
            expires_at = datetime.utcnow() + timedelta(days=365 * 10)
            admin_user = User(
                id="admin",
                name="系统管理员",
                hashed_password=get_password_hash("admin123"),
                level=UserLevel.ADMIN,
                group_id=None,
                granted_by="system",
                expires_at=expires_at,
                status="ACTIVE"
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created: admin / admin123")
    finally:
        db.close()


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    log_action(db, user.id, "PC", LogAction.LOGIN, "PC")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        level=current_user.level,
        group_id=current_user.group_id,
        status=current_user.status
    )


@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check permissions
    if current_user.level not in [UserLevel.ADMIN, UserLevel.GROUP_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to create users")
    
    if get_user(db, user.id):
        raise HTTPException(status_code=400, detail="User ID already registered")
    
    expires_at = datetime.utcnow() + timedelta(days=user.expires_in_days)
    db_user = User(
        id=user.id,
        name=user.name,
        hashed_password=get_password_hash(user.password),
        level=user.level,
        group_id=user.group_id,
        granted_by=current_user.id,
        expires_at=expires_at,
        status="ACTIVE"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    log_action(db, current_user.id, "SERVER", LogAction.PERM, f"Created user: {user.id}")
    return UserResponse(
        id=db_user.id,
        name=db_user.name,
        level=db_user.level,
        group_id=db_user.group_id,
        status=db_user.status
    )


@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    zone: str = Form(...),
    path: str = Form(...),
    metadata: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_id = str(uuid.uuid4())
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Save file to storage
    storage_path = os.path.join(STORAGE_DIR, file_id)
    with open(storage_path, "wb") as f:
        f.write(content)
    
    # Parse metadata
    metadata_dict = json.loads(metadata) if metadata else None
    
    # Create file record
    db_file = File(
        id=file_id,
        zone=FileZone.DATA if zone == "DATA" else FileZone.COLLABORATION,
        name=file.filename,
        path=path,
        size=len(content),
        hash=file_hash,
        owner_id=current_user.id,
        edited=False,
        edit_count=0,
        uploader=current_user.id,
        source_device="PC",
        source_type=SourceType.PC,
        metadata=json.dumps(metadata_dict) if metadata_dict else None,
        status=FileStatus.ACTIVE
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    if zone == "DATA":
        log_action(db, current_user.id, "PC", LogAction.ADD, file.filename)
    else:
        log_action(db, current_user.id, "PC", LogAction.COLLAB_ADD, f"{current_user.id}:{file.filename}")
    
    return {"file_id": file_id, "message": "File uploaded successfully"}


@app.get("/files", response_model=List[FileResponse])
def list_files(
    zone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(File).filter(File.status == FileStatus.ACTIVE)
    
    if zone:
        query = query.filter(File.zone == zone)
    
    # Filter by permissions (simplified)
    if current_user.level == UserLevel.ADMIN:
        pass  # Can see all
    elif current_user.level == UserLevel.GROUP_ADMIN:
        # Can see group members' files
        group_users = db.query(User).filter(User.group_id == current_user.group_id).all()
        user_ids = [u.id for u in group_users]
        query = query.filter((File.owner_id == current_user.id) | (File.owner_id.in_(user_ids)))
    else:
        # Can see own files
        query = query.filter(File.owner_id == current_user.id)
    
    files = query.order_by(File.upload_time.desc()).all()
    
    responses = []
    for f in files:
        metadata = json.loads(f.metadata) if f.metadata else None
        responses.append(FileResponse(
            id=f.id,
            zone=f.zone.value,
            name=f.name,
            path=f.path,
            size=f.size,
            owner_id=f.owner_id,
            edited=f.edited,
            edit_count=f.edit_count,
            uploader=f.uploader,
            upload_time=f.upload_time,
            source_type=f.source_type.value,
            metadata=metadata
        ))
    return responses


@app.get("/files/{file_id}")
def get_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from fastapi.responses import FileResponse
    
    file = db.query(File).filter(File.id == file_id, File.status == FileStatus.ACTIVE).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions
    if current_user.level != UserLevel.ADMIN and file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")
    
    storage_path = os.path.join(STORAGE_DIR, file_id)
    if not os.path.exists(storage_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    if file.zone == FileZone.DATA:
        log_action(db, current_user.id, "PC", LogAction.ADD, f"Downloaded: {file.name}")
    else:
        log_action(db, current_user.id, "PC", LogAction.COLLAB_DOWNLOAD, f"{current_user.id}:{file.name}")
    
    return FileResponse(path=storage_path, filename=file.name)


@app.delete("/files/{file_id}")
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions
    if current_user.level == UserLevel.MEMBER and file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")
    
    file.status = FileStatus.DELETED
    db.commit()
    
    log_action(db, current_user.id, "SERVER", LogAction.DEL, file.name)
    return {"message": "File deleted successfully"}


@app.get("/logs")
def get_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Log).order_by(Log.timestamp.desc())
    
    if current_user.level == UserLevel.MEMBER:
        query = query.filter(Log.operator == current_user.id)
    elif current_user.level == UserLevel.GROUP_ADMIN:
        group_users = db.query(User).filter(User.group_id == current_user.group_id).all()
        user_ids = [u.id for u in group_users] + [current_user.id]
        query = query.filter(Log.operator.in_(user_ids))
    
    logs = query.limit(limit).all()
    return [{"id": l.id, "timestamp": l.timestamp, "operator": l.operator, 
             "location": l.location, "action": l.action.value, "detail": l.detail} 
            for l in logs]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
