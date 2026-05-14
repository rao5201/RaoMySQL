"""RaoMySQL Alerts Router v1.2 - 告警管理 + Async DB + current_user.id Fix"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from backend.database.init_db import get_db
from backend.database.models import Alert, DbConnection, User
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["告警"])

class AlertCreate(BaseModel):
    connection_id: Optional[int] = None
    level: str          # info / warning / critical
    title: str
    content: Optional[str] = None

class AlertUpdate(BaseModel):
    level: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None  # unread / read / resolved

class AlertResponse(BaseModel):
    id: int; connection_id: Optional[int]; level: str; title: str
    content: Optional[str]; status: str; created_at: str

    class Config:
        from_attributes = True

def _alert_to_dict(a: Alert) -> dict:
    return {
        "id": a.id, "connection_id": a.connection_id,
        "level": a.level, "title": a.title,
        "content": a.content, "status": a.status,
        "created_at": str(a.created_at)
    }

@router.get("")
async def list_alerts(
    level: Optional[str] = None,
    status: Optional[str] = None,
    connection_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """查询告警列表（用户只能看自己的，admin 可看全部）"""
    if current.role == "admin":
        q = select(Alert)
        if connection_id:
            q = q.where(Alert.connection_id == connection_id)
    else:
        q = select(Alert).where(Alert.user_id == current.id)
        if connection_id:
            q = q.where(Alert.connection_id == connection_id)

    if level:   q = q.where(Alert.level == level)
    if status:   q = q.where(Alert.status == status)

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar()
    items = (await db.execute(
        q.order_by(Alert.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    )).scalars().all()

    # 填充连接名称（仅 admin 可见全部连接名）
    results = []
    for a in items:
        item = _alert_to_dict(a)
        if a.connection_id:
            cr = await db.execute(select(DbConnection.name).where(DbConnection.id == a.connection_id))
            item["connection_name"] = cr.scalar()
        results.append(item)

    return {"total": total, "page": page, "data": results}

@router.post("")
async def create_alert(
    data: AlertCreate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建告警（admin 可为任意用户创建，普通用户只能创建自己的）"""
    # 连接归属检查
    if data.connection_id:
        conn_q = select(DbConnection).where(DbConnection.id == data.connection_id)
        if current.role != "admin":
            conn_q = conn_q.where(DbConnection.user_id == current.id)
        conn = (await db.execute(conn_q)).scalar_one_or_none()
        if not conn:
            raise HTTPException(status_code=404, detail="连接不存在或无权使用")

    alert = Alert(
        user_id=current.id,
        connection_id=data.connection_id,
        level=data.level,
        title=data.title,
        content=data.content,
        status="unread"
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return _alert_to_dict(alert)

@router.get("/{aid}")
async def get_alert(
    aid: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Alert).where(Alert.id == aid))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    if current.role != "admin" and alert.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限访问")
    return _alert_to_dict(alert)

@router.put("/{aid}")
async def update_alert(
    aid: int,
    data: AlertUpdate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新告警（用户只能更新自己的，admin 可更新任意）"""
    result = await db.execute(select(Alert).where(Alert.id == aid))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    if current.role != "admin" and alert.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(alert, field, value)
    await db.commit()
    return _alert_to_dict(alert)

@router.put("/{aid}/read")
async def mark_read(
    aid: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Alert).where(Alert.id == aid))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    if current.role != "admin" and alert.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")
    alert.status = "read"
    await db.commit()
    return {"message": "已标记为已读"}

@router.put("/{aid}/resolve")
async def resolve_alert(
    aid: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Alert).where(Alert.id == aid))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    if current.role != "admin" and alert.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")
    alert.status = "resolved"
    await db.commit()
    return {"message": "已标记为已解决"}

@router.put("/batch/read")
async def mark_all_read(
    alert_ids: list[int],
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量标记已读"""
    for aid in alert_ids:
        result = await db.execute(select(Alert).where(Alert.id == aid))
        alert = result.scalar_one_or_none()
        if alert and (current.role == "admin" or alert.user_id == current.id):
            alert.status = "read"
    await db.commit()
    return {"message": f"已标记 {len(alert_ids)} 条为已读"}

@router.delete("/{aid}")
async def delete_alert(
    aid: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可删除告警")
    result = await db.execute(select(Alert).where(Alert.id == aid))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    await db.delete(alert)
    await db.commit()
    return {"message": "已删除"}

@router.get("/stats/summary")
async def alert_stats(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """告警统计摘要"""
    uid_filter = () if current.role == "admin" else (Alert.user_id == current.id,)
    total = (await db.execute(
        select(func.count()).select_from(Alert).where(*uid_filter)
    )).scalar()
    unread = (await db.execute(
        select(func.count()).select_from(Alert).where(
            Alert.status == "unread", *uid_filter
        )
    )).scalar()
    critical_unread = (await db.execute(
        select(func.count()).select_from(Alert).where(
            Alert.level == "critical", Alert.status == "unread", *uid_filter
        )
    )).scalar()
    warning_unread = (await db.execute(
        select(func.count()).select_from(Alert).where(
            Alert.level == "warning", Alert.status == "unread", *uid_filter
        )
    )).scalar()
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today = (await db.execute(
        select(func.count()).select_from(Alert).where(
            Alert.created_at >= today_start, *uid_filter
        )
    )).scalar()
    return {
        "total": total, "unread": unread,
        "critical_unread": critical_unread, "warning_unread": warning_unread,
        "today": today
    }

@router.post("/auto-create")
async def auto_create_alert(
    connection_id: int,
    level: str,
    title: str,
    content: str,
    db: AsyncSession = Depends(get_db)
):
    """
    供 monitor.py / tasks.py 等内部模块调用，
    当检测到异常时自动创建告警（无需认证，internal 调用）。
    """
    alert = Alert(
        user_id=0,   # system alert
        connection_id=connection_id,
        level=level, title=title, content=content, status="unread"
    )
    db.add(alert)
    await db.commit()
    return {"message": "alert created"}
