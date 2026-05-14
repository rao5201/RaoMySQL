"""RaoMySQL Monitor Router v1.2 - Async DB + current_user.id Fix"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from backend.database.init_db import get_db
from backend.database.models import DbConnection, Alert, User
from .auth import get_current_user
from backend.utils.crypto import decrypt_password
from backend.services.mysql_client import MySQLClient

router = APIRouter(prefix="/api/monitor", tags=["Monitor"])

class AlertCreate(BaseModel):
    connection_id: Optional[int] = None
    level: str
    title: str
    content: Optional[str] = None

def _creds(conn: DbConnection) -> dict:
    pw = decrypt_password(conn.password_enc) if conn.password_enc else ""
    return {"host": conn.host, "port": conn.port, "user": conn.username,
            "pw": pw, "database": conn.database_name}

async def _get_conn_creds(cid: int, current: User, db: AsyncSession):
    result = await db.execute(select(DbConnection).where(
        DbConnection.id == cid, DbConnection.user_id == current.id))
    conn = result.scalar_one_or_none()
    if not conn: raise HTTPException(status_code=404, detail="connection not found")
    return conn, _creds(conn)

@router.get("/{cid}/status")
async def get_status(cid: int, current: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    _, cr = await _get_conn_creds(cid, current, db)
    try:
        return await MySQLClient.get_status(cid, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/{cid}/slow-queries")
async def get_slow_queries(cid: int, limit: int = 10,
                         current: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    _, cr = await _get_conn_creds(cid, current, db)
    try:
        rows = await MySQLClient.get_slow_queries(cid, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"], limit)
        return {"connection_id": cid, "queries": rows, "total": len(rows)}
    except Exception as e:
        return {"connection_id": cid, "queries": [], "total": 0, "error": str(e)}

@router.get("/{cid}/capacity")
async def get_capacity(cid: int, current: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    _, cr = await _get_conn_creds(cid, current, db)
    try:
        return await MySQLClient.get_capacity(cid, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
    except Exception as e:
        return {"error": str(e)}

@router.get("/health")
async def get_health(current: User = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbConnection).where(DbConnection.user_id == current.id))
    conns = result.scalars().all()
    results = []
    for c in conns:
        cr = _creds(c)
        try:
            st = await MySQLClient.get_status(c.id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
            results.append({"id": c.id, "name": c.name, **st})
        except Exception:
            results.append({"id": c.id, "name": c.name, "status": "error"})
    healthy = sum(1 for r in results if r.get("status") == "connected")
    return {"total": len(results), "healthy": healthy, "connections": results,
            "score": round(healthy/len(results)*100, 1) if results else 100}

@router.get("/alerts")
async def get_alerts(level: Optional[str] = None, status: Optional[str] = None,
                     page: int = 1, page_size: int = 20,
                     current: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    q = select(Alert).where(Alert.user_id == current.id)
    if level: q = q.where(Alert.level == level)
    if status: q = q.where(Alert.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    items = (await db.execute(
        q.order_by(Alert.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    )).scalars().all()
    return {"total": total, "data": items}

@router.post("/alerts")
async def create_alert(alert_data: AlertCreate, current: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    alert = Alert(user_id=current.id, connection_id=alert_data.connection_id,
        level=alert_data.level, title=alert_data.title, content=alert_data.content, status="unread")
    db.add(alert); await db.commit(); await db.refresh(alert)
    return alert

@router.put("/alerts/{aid}/read")
async def mark_read(aid: int, current: User = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(
        Alert.id == aid, Alert.user_id == current.id))
    alert = result.scalar_one_or_none()
    if not alert: raise HTTPException(status_code=404, detail="not found")
    alert.status = "read"; await db.commit()
    return {"message": "marked as read"}

@router.put("/alerts/{aid}/resolve")
async def resolve_alert(aid: int, current: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(
        Alert.id == aid, Alert.user_id == current.id))
    alert = result.scalar_one_or_none()
    if not alert: raise HTTPException(status_code=404, detail="not found")
    alert.status = "resolved"; await db.commit()
    return {"message": "resolved"}

@router.get("/alerts/stats")
async def alert_stats(current: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    uid = current.id
    total = (await db.execute(select(func.count()).select_from(Alert).where(Alert.user_id == uid))).scalar()
    unread = (await db.execute(select(func.count()).select_from(Alert).where(
        Alert.user_id == uid, Alert.status == "unread"))).scalar()
    critical = (await db.execute(select(func.count()).select_from(Alert).where(
        Alert.user_id == uid, Alert.level == "critical", Alert.status == "unread"))).scalar()
    return {"total": total, "unread": unread, "critical": critical}
