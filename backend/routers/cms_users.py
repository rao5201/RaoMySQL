"""
RaoCMS - 用户管理路由
后台用户管理、前台注册用户管理
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.database.cms_models import SysUser, PortalUser, OperationLog
from .cms_auth import get_current_user, require_admin, UserRole, Permission, require_permissions, get_password_hash
from backend.database.init_db import get_db

router = APIRouter(prefix="/api", tags=["用户管理"])


# ==================== Pydantic 模型 ====================

class SysUserCreate(BaseModel):
    username: str
    password: str
    real_name: Optional[str] = None
    role: str = "customer_service"
    email: Optional[str] = None
    phone: Optional[str] = None


class SysUserUpdate(BaseModel):
    real_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class PortalUserUpdate(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    user_tags: Optional[str] = None
    status: Optional[str] = None


class SysUserResponse(BaseModel):
    id: int
    username: str
    real_name: Optional[str]
    role: str
    email: Optional[str]
    phone: Optional[str]
    status: str
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PortalUserResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    status: str
    user_tags: Optional[str]
    register_ip: Optional[str]
    last_login: Optional[datetime]
    login_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 后台用户管理 ====================

@router.get("/users", response_model=List[SysUserResponse])
async def get_sys_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取后台用户列表（仅管理员）"""
    query = db.query(SysUser)
    
    if role:
        query = query.filter(SysUser.role == role)
    if status:
        query = query.filter(SysUser.status == status)
    if keyword:
        query = query.filter(
            (SysUser.username.contains(keyword)) | 
            (SysUser.real_name.contains(keyword))
        )
    
    total = query.count()
    users = query.order_by(SysUser.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return users


@router.post("/users", response_model=SysUserResponse)
async def create_sys_user(
    user_data: SysUserCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """创建后台用户（仅管理员）"""
    # 检查用户名是否存在
    existing = db.query(SysUser).filter(SysUser.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 验证角色
    valid_roles = [r.value for r in UserRole]
    if user_data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"无效的角色: {user_data.role}")
    
    user = SysUser(
        username=user_data.username,
        password=get_password_hash(user_data.password),
        real_name=user_data.real_name,
        role=user_data.role,
        email=user_data.email,
        phone=user_data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/users/{user_id}", response_model=SysUserResponse)
async def get_sys_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取后台用户详情"""
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/users/{user_id}", response_model=SysUserResponse)
async def update_sys_user(
    user_id: int,
    user_data: SysUserUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新后台用户"""
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能修改自己的角色（防止失去管理员权限）
    if user_id == current_user.get("id") and user_data.role and user_data.role != user.role:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    
    update_data = user_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
async def delete_sys_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除后台用户"""
    if user_id == current_user.get("id"):
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}


# ==================== 前台用户管理 ====================

@router.get("/portal/users", response_model=List[PortalUserResponse])
async def get_portal_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: dict = Depends(require_permissions([Permission.PORTAL_USER_VIEW])),
    db: Session = Depends(get_db)
):
    """获取前台注册用户列表"""
    query = db.query(PortalUser)
    
    if status:
        query = query.filter(PortalUser.status == status)
    if keyword:
        query = query.filter(
            (PortalUser.username.contains(keyword)) |
            (PortalUser.nickname.contains(keyword)) |
            (PortalUser.email.contains(keyword))
        )
    
    total = query.count()
    users = query.order_by(PortalUser.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return users


@router.get("/portal/users/{user_id}", response_model=PortalUserResponse)
async def get_portal_user(
    user_id: int,
    current_user: dict = Depends(require_permissions([Permission.PORTAL_USER_VIEW])),
    db: Session = Depends(get_db)
):
    """获取前台用户详情"""
    user = db.query(PortalUser).filter(PortalUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/portal/users/{user_id}", response_model=PortalUserResponse)
async def update_portal_user(
    user_id: int,
    user_data: PortalUserUpdate,
    current_user: dict = Depends(require_permissions([Permission.PORTAL_USER_MANAGE])),
    db: Session = Depends(get_db)
):
    """更新前台用户"""
    user = db.query(PortalUser).filter(PortalUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    update_data = user_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.get("/portal/users/stats")
async def get_portal_user_stats(
    current_user: dict = Depends(require_permissions([Permission.PORTAL_USER_VIEW])),
    db: Session = Depends(get_db)
):
    """获取前台用户统计"""
    from sqlalchemy import func
    
    # 总用户数
    total = db.query(func.count(PortalUser.id)).scalar()
    
    # 今日新增
    today = datetime.utcnow().date()
    today_new = db.query(func.count(PortalUser.id)).filter(
        func.date(PortalUser.created_at) == today
    ).scalar()
    
    # 活跃用户（30天内登录过）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active = db.query(func.count(PortalUser.id)).filter(
        PortalUser.last_login >= thirty_days_ago
    ).scalar()
    
    # 按状态统计
    active_count = db.query(func.count(PortalUser.id)).filter(PortalUser.status == "active").scalar()
    disabled_count = db.query(func.count(PortalUser.id)).filter(PortalUser.status == "disabled").scalar()
    
    return {
        "total": total,
        "today_new": today_new,
        "active_30d": active,
        "active_count": active_count,
        "disabled_count": disabled_count
    }


# ==================== 操作日志 ====================

@router.get("/users/{user_id}/logs")
async def get_user_logs(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取用户操作日志"""
    logs = db.query(OperationLog).filter(
        OperationLog.user_id == user_id
    ).order_by(OperationLog.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return logs


from datetime import timedelta
