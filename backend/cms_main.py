"""
RaoCMS - 主入口
企业网站后台管理系统
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.init_db import get_db, init_cms_db
from backend.routers.cms_auth import router as auth_router
from backend.routers.cms_articles import router as articles_router
from backend.routers.cms_users import router as users_router
from backend.routers.cms_supplier import router as supplier_router
from backend.routers.cms_finance import router as finance_router
import os

# 初始化数据库
init_cms_db()

app = FastAPI(
    title="RaoCMS API",
    description="企业网站后台管理系统 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(articles_router, tags=["文章管理"])
app.include_router(users_router, tags=["用户管理"])
app.include_router(supplier_router, tags=["供应商/产品管理"])
app.include_router(finance_router, tags=["财务管理"])


@app.get("/")
async def root():
    return {"message": "RaoCMS API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)