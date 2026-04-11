"""RaoMySQL Audit Router - Operation logging and query"""
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database.init_db import get_db
from backend.database.audit_log import AuditLog
from .auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["Audit"])

class AuditQuery(BaseModel):
    action: Optional[str] = None
    username: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    keyword: Optional[str] = None

def log_action(db: Session, user_id, username, action, resource=None,
               detail=None, ip=None, status="success"):
    """Write an audit log entry. Call from any router after operation."""
    entry = AuditLog(
        user_id=user_id, username=username, action=action,
        resource=str(resource)[:200] if resource else None,
        detail=json.dumps(detail, ensure_ascii=False, default=str) if detail else None,
        ip_address=ip, status=status
    )
    db.add(entry)
    db.commit()

def log_failed(db: Session, user_id, username, action, resource=None,
               detail=None, ip=None):
    """Log a failed operation."""
    log_action(db, user_id, username, action, resource, detail, ip, "failed")

def log_denied(db: Session, user_id, username, action, resource=None,
               detail=None, ip=None):
    """Log a permission denied operation."""
    log_action(db, user_id, username, action, resource, detail, ip, "denied")

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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query audit logs (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(403, "admin only")
    q = db.query(AuditLog)
    if action: q = q.filter(AuditLog.action == action)
    if username: q = q.filter(AuditLog.username == username)
    if status: q = q.filter(AuditLog.status == status)
    if start_date:
        try: q = q.filter(AuditLog.created_at >= datetime.fromisoformat(start_date))
        except: pass
    if end_date:
        try: q = q.filter(AuditLog.created_at <= datetime.fromisoformat(end_date))
        except: pass
    if keyword: q = q.filter(AuditLog.detail.like(f"%{keyword}%"))
    total = q.count()
    items = q.order_by(AuditLog.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "page": page, "data": [i.to_dict() for i in items]}

@router.get("/stats")
async def audit_stats(current_user=Depends(get_current_user), db=Depends(get_db)):
    """Audit statistics dashboard"""
    if current_user.get("role") != "admin":
        raise HTTPException(403, "admin only")
    from sqlalchemy import func
    total = db.query(AuditLog).count()
    today = db.query(AuditLog).filter(
        AuditLog.created_at >= datetime.now().replace(hour=0,minute=0,second=0)).count()
    failed = db.query(AuditLog).filter(AuditLog.status == "failed").count()
    denied = db.query(AuditLog).filter(AuditLog.status == "denied").count()
    # Top actions
    actions = db.query(AuditLog.action, func.count(AuditLog.id).label("cnt")).group_by(
        AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(10).all()
    # Top users
    users = db.query(AuditLog.username, func.count(AuditLog.id).label("cnt")).group_by(
        AuditLog.username).order_by(func.count(AuditLog.id).desc()).limit(10).all()
    return {"total": total, "today": today, "failed": failed, "denied": denied,
            "top_actions": [{"action":a,"count":c} for a,c in actions],
            "top_users": [{"username":u,"count":c} for u,c in users]}

@router.delete("/logs/cleanup")
async def cleanup_logs(days: int = 90, current_user=Depends(get_current_user), db=Depends(get_db)):
    """Delete audit logs older than N days (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(403, "admin only")
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    deleted = db.query(AuditLog).filter(AuditLog.created_at < cutoff).delete()
    db.commit()
    return {"deleted": deleted, "cutoff": cutoff.isoformat()}
