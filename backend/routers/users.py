"""用户管理路由 - 管理员专用"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from backend.database.init_db import get_db
from backend.database.models import User
from .auth import get_current_admin, get_current_user, hash_password, verify_password
from pydantic import BaseModel

router = APIRouter(prefix="/api/users", tags=["用户管理"])

# ---- Schemas ----
class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

class UserCreateByAdmin(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "viewer"

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[str]
    status: str
    created_at: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class AdminPasswordReset(BaseModel):
    new_password: str

# ---- 管理员接口 ----

@router.get("", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """获取用户列表（管理员）"""
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if status:
        query = query.where(User.status == status)
    if keyword:
        query = query.where(User.username.contains(keyword))

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {"id": u.id, "username": u.username, "role": u.role,
             "email": u.email, "status": u.status, "created_at": str(u.created_at)}
            for u in users
        ]
    }

@router.post("", response_model=dict)
async def create_user(
    data: UserCreateByAdmin,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """管理员创建用户"""
    exists = await db.execute(select(User).where(User.username == data.username))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username,
        password=hash_password(data.password),
        email=data.email,
        role=data.role,
        status="active"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role,
            "email": user.email, "status": user.status, "created_at": str(user.created_at)}

@router.get("/stats/overview")
async def user_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """用户统计概览"""
    total = (await db.execute(select(func.count(User.id)))).scalar()
    active = (await db.execute(select(func.count(User.id)).where(User.status == "active"))).scalar()
    disabled = (await db.execute(select(func.count(User.id)).where(User.status == "disabled"))).scalar()
    by_role = {}
    for role in ["admin", "viewer", "editor"]:
        cnt = (await db.execute(select(func.count(User.id)).where(User.role == role))).scalar()
        by_role[role] = cnt
    return {"total": total, "active": active, "disabled": disabled, "by_role": by_role}

@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"id": user.id, "username": user.username, "role": user.role,
            "email": user.email, "status": user.status, "created_at": str(user.created_at)}

@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_admin)
):
    """管理员修改用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.email is not None:
        user.email = data.email
    if data.role is not None:
        if user_id == current.id and data.role != "admin":
            raise HTTPException(status_code=400, detail="不能修改自己的角色")
        user.role = data.role
    if data.status is not None:
        if user_id == current.id:
            raise HTTPException(status_code=400, detail="不能禁用自己")
        user.status = data.status
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role,
            "email": user.email, "status": user.status, "created_at": str(user.created_at)}

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_admin)
):
    """管理员删除用户"""
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    await db.delete(user)
    await db.commit()
    return {"message": "用户已删除"}

@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    data: AdminPasswordReset,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """管理员重置用户密码"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password = hash_password(data.new_password)
    await db.commit()
    return {"message": "密码已重置"}

@router.post("/{user_id}/toggle-status")
async def toggle_status(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_admin)
):
    """启用/禁用用户"""
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="不能操作自己")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.status = "disabled" if user.status == "active" else "active"
    await db.commit()
    label = "禁用" if user.status == "disabled" else "启用"
    return {"message": f"用户已{label}", "status": user.status}

# ---- 普通用户接口 ----

@router.post("/me/change-password")
async def change_password(
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user)
):
    """用户修改自己的密码"""
    if not verify_password(data.old_password, current.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    current.password = hash_password(data.new_password)
    await db.commit()
    return {"message": "密码已修改"}
