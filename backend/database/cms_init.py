"""
RaoMySQL/RaoCMS 数据库初始化
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/raocms.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化 MySQL 管理数据库"""
    from .models import Base
    Base.metadata.create_all(bind=engine)


def init_cms_db():
    """初始化 CMS 数据库"""
    os.makedirs("data", exist_ok=True)
    from backend.cms_models import Base
    Base.metadata.create_all(bind=engine)


# 初始化默认管理员账号
def create_default_admin():
    """创建默认管理员账号"""
    from backend.routers.cms_auth import get_password_hash
    from backend.cms_models import SysUser
    
    db = SessionLocal()
    try:
        # 检查是否已存在管理员
        admin = db.query(SysUser).filter(SysUser.username == "admin").first()
        if not admin:
            admin = SysUser(
                username="admin",
                password=get_password_hash("admin123"),
                real_name="系统管理员",
                role="admin",
                status="active"
            )
            db.add(admin)
            db.commit()
            print("✅ 默认管理员账号已创建: admin / admin123")
    finally:
        db.close()


if __name__ == "__main__":
    init_cms_db()
    create_default_admin()
    print("✅ 数据库初始化完成")