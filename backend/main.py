"""RaoMySQL 后端服务入口"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import settings
from database.init_db import init_db
from services.mysql_client import mysql_client
from routers.auth import router as auth_router
from routers.connections import router as connections_router
from routers.sql import router as sql_router

# AI / 备份 / 任务 / 监控 / 告警 路由（Phase 2-4 实现）
# from routers.ai import router as ai_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    await init_db()
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[RaoMySQL] 服务启动成功，访问 http://localhost:8000")
    print(f"[RaoMySQL] API 文档 http://localhost:8000/docs")
    yield
    # 关闭：关闭所有 MySQL 连接池
    await mysql_client.close_all()
    print("[RaoMySQL] 服务已关闭")

app = FastAPI(
    title=settings.APP_NAME,
    description="私有 MySQL 数据库管理平台 API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS：允许前端本地开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(connections_router)
app.include_router(sql_router)

# 健康检查
@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}

@app.get("/")
async def root():
    return {
        "message": "RaoMySQL API",
        "docs": "/docs",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
