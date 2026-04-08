"""RaoMySQL v1.2.0 Backend Entry"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from config import settings
from database.init_db import init_db
from services.mysql_client import mysql_client
from routers.auth import router as auth_router
from routers.connections import router as connections_router
from routers.sql import router as sql_router
from routers.backups import router as backups_router
from routers.monitor import router as monitor_router
from routers.tasks import router as tasks_router
from routers.ai import router as ai_router
from routers.audit import router as audit_router
from routers.export import router as export_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[RaoMySQL v1.2.0] http://localhost:{settings.PORT}")
    print(f"[RaoMySQL v1.2.0] API Docs http://localhost:{settings.PORT}/docs")
    yield
    await mysql_client.close_all()
    print("[RaoMySQL] shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    description="RaoMySQL v1.2.0 - Private MySQL Management + Enterprise CMS",
    version="1.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
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
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.2.0"}

@app.get("/")
async def root():
    return {"message": "RaoMySQL API v1.2.0", "docs": "/docs", "version": "1.2.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
