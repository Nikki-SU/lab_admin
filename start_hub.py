#!/usr/bin/env python3
import uvicorn
from hub.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "hub.app:app",
        host=settings.HUB_HOST,
        port=settings.HUB_PORT,
        reload=True
    )
