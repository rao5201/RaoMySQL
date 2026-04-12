"""RaoMySQL v1.6.0 Backend Entry"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database.init_db import init_db
from backend.services.mysql_client import mysql_client
from backend.routers.auth import router as auth_router
from backend.routers.users import router as users_router
from backend.routers.connections import router as connections_router
from backend.routers.sql import router as sql_router
from backend.routers.backups import router as backups_router
from backend.routers.monitor import router as monitor_router
from backend.routers.tasks import router as tasks_router
from backend.routers.ai import router as ai_router
from backend.routers.audit import router as audit_router
from backend.routers.export import router as export_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[RaoMySQL v1.6.0] http://localhost:{8000}")
    print(f"[RaoMySQL v1.6.0] API Docs http://localhost:{8000}/docs")
    yield
    await mysql_client.close_all()
    print("[RaoMySQL] shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    description="RaoMySQL v1.6.0 - Private MySQL Management + Enterprise CMS + User Management",
    version="1.6.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(connections_router, prefix="/api")
app.include_router(sql_router, prefix="/api")
app.include_router(backups_router)
app.include_router(monitor_router)
app.include_router(tasks_router)
app.include_router(ai_router)
app.include_router(audit_router)
app.include_router(export_router)

@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.6.0"}

@app.get("/")
async def root():
    return {"message": "RaoMySQL API v1.6.0", "docs": "/docs", "version": "1.6.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)
