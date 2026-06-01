from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, users, files, devices, shares, logs

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LabVault Hub Server", version="1.0")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(shares.router, prefix="/api/shares", tags=["shares"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])


@app.get("/")
async def root():
    return {"message": "LabVault Hub Server is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
