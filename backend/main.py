"""RaoMySQL v1.6.0 Backend Entry"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from threading import Lock
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.database.init_db import init_db
from backend.database.models import User
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

# ── 速率限制（防暴力破解：每 IP 每分钟 10 次） ──
class RateLimitMiddleware:
    def __init__(self):
        self._counts: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
        self._limit = 10   # 次
        self._window = 60  # 秒

    def check(self, client_ip: str) -> bool:
        now = time.time()
        with self._lock:
            self._counts[client_ip] = [
                t for t in self._counts[client_ip] if now - t < self._window
            ]
            if len(self._counts[client_ip]) >= self._limit:
                return False
            self._counts[client_ip].append(now)
            return True

rate_limiter = RateLimitMiddleware()

# ── 启动/关闭 ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[RaoMySQL v1.6.0] http://localhost:8000")
    print(f"[RaoMySQL v1.6.0] API Docs http://localhost:8000/docs")
    yield
    await mysql_client.close_all()
    print("[RaoMySQL] shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    description="RaoMySQL v1.6.0 — 开源 MySQL 数据库管理平台 + 企业 CMS + 用户管理",
    version="1.6.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS（安全配置：allow_credentials 不与 * 混用） ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── 全局速率限制中间件 ──
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    if path in ("/api/auth/login", "/api/auth/register", "/api/auth/register-with-invite"):
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.check(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试（限速：10次/分钟）"}
            )
    response = await call_next(request)
    return response

# ── 注册路由 ──
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
    return {
        "message": "RaoMySQL API v1.6.0",
        "docs": "/docs",
        "github": "https://github.com/rao5201/RaoMySQL",
        "version": "1.6.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)
