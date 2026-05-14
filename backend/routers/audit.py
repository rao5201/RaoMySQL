"""RaoMySQL Audit Router v1.2 - Async DB + current_user.id Fix"""
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from backend.database.init_db import get_db
from backend.database.audit_log import AuditLog
from backend.database.models import User
from .auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["Audit"])

class AuditQuery(BaseModel):
    action: Optional[str] = None
    username: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    keyword: Optional[str] = None

async def log_action(db: AsyncSession, user_id: int, username: str,
                     action: str, resource=None, detail=None,
                     ip: str = None, status: str = "success"):
    """Write an audit log entry."""
    entry = AuditLog(
        user_id=user_id, username=username, action=action,
        resource=str(resource)[:200] if resource else None,
        detail=json.dumps(detail, ensure_ascii=False, default=str) if detail else None,
        ip_address=ip, status=status
    )
    db.add(entry)
    await db.commit()

@router.get("/logs")
async def get_logs(
    action: Optional[str] = None,
    username: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Query audit logs (admin only)"""
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="admin only")

    q = select(AuditLog)
    if action: q = q.where(AuditLog.action == action)
    if username: q = q.where(AuditLog.username == username)
    if status: q = q.where(AuditLog.status == status)
    if start_date:
        try: q = q.where(AuditLog.created_at >= datetime.fromisoformat(start_date))
        except: pass
    if end_date:
        try: q = q.where(AuditLog.created_at <= datetime.fromisoformat(end_date))
        except: pass
    if keyword: q = q.where(AuditLog.detail.like(f"%{keyword}%"))

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    items = (await db.execute(
        q.order_by(AuditLog.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    )).scalars().all()
    return {"total": total, "page": page, "data": [i.to_dict() for i in items]}

@router.get("/stats")
async def audit_stats(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Audit statistics dashboard"""
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="admin only")

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total = (await db.execute(select(func.count()).select_from(AuditLog))).scalar()
    today = (await db.execute(
        select(func.count()).select_from(AuditLog).where(AuditLog.created_at >= today_start)
    )).scalar()
    failed = (await db.execute(
        select(func.count()).select_from(AuditLog).where(AuditLog.status == "failed")
    )).scalar()
    denied = (await db.execute(
        select(func.count()).select_from(AuditLog).where(AuditLog.status == "denied")
    )).scalar()

    actions = (await db.execute(
        select(AuditLog.action, func.count(AuditLog.id).label("cnt"))
            .group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(10)
    )).all()
    users = (await db.execute(
        select(AuditLog.username, func.count(AuditLog.id).label("cnt"))
            .group_by(AuditLog.username).order_by(func.count(AuditLog.id).desc()).limit(10)
    )).all()

    return {
        "total": total, "today": today, "failed": failed, "denied": denied,
        "top_actions": [{"action": a, "count": int(c)} for a, c in actions],
        "top_users": [{"username": u, "count": int(c)} for u, c in users]
    }

@router.delete("/logs/cleanup")
async def cleanup_logs(
    days: int = 90,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete audit logs older than N days (admin only)"""
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    await db.execute(
        select(AuditLog).where(AuditLog.created_at < cutoff).delete(synchronize_session=False)
    )
    await db.commit()
    return {"deleted": "cleanup done", "cutoff": cutoff.isoformat()}
