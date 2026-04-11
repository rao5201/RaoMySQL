"""RaoMySQL Monitor Router v1.1 - Live metrics via mysql_client"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.database.init_db import get_db
from backend.database.models import DbConnection, Alert
from .auth import get_current_user
from backend.utils.crypto import decrypt_password
from backend.services.mysql_client import MySQLClient

router = APIRouter(prefix="/api/monitor", tags=["Monitor"])

class AlertCreate(BaseModel):
    connection_id: Optional[int] = None
    level: str
    title: str
    content: Optional[str] = None

def _get_conn_creds(conn):
    pw = decrypt_password(conn.password_enc) if conn.password_enc else ""
    return {"host": conn.host, "port": conn.port, "user": conn.username,
            "pw": pw, "database": conn.database}

@router.get("/{cid}/status")
async def get_status(cid: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    conn = db.query(DbConnection).filter(
        DbConnection.id == cid, DbConnection.user_id == current_user.get("id")).first()
    if not conn: raise HTTPException(404, "connection not found")
    cr = _get_conn_creds(conn)
    try:
        return await MySQLClient.get_status(cid, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/{cid}/slow-queries")
async def get_slow_queries(cid: int, limit=10, current_user=Depends(get_current_user), db=Depends(get_db)):
    conn = db.query(DbConnection).filter(
        DbConnection.id == cid, DbConnection.user_id == current_user.get("id")).first()
    if not conn: raise HTTPException(404, "connection not found")
    cr = _get_conn_creds(conn)
    try:
        rows = await MySQLClient.get_slow_queries(cid, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"], limit)
        return {"connection_id": cid, "queries": rows, "total": len(rows)}
    except Exception as e:
        return {"connection_id": cid, "queries": [], "total": 0, "error": str(e)}

@router.get("/{cid}/capacity")
async def get_capacity(cid: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    conn = db.query(DbConnection).filter(
        DbConnection.id == cid, DbConnection.user_id == current_user.get("id")).first()
    if not conn: raise HTTPException(404, "connection not found")
    cr = _get_conn_creds(conn)
    try:
        return await MySQLClient.get_capacity(cid, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
    except Exception as e:
        return {"error": str(e)}

@router.get("/health")
async def get_health(current_user=Depends(get_current_user), db=Depends(get_db)):
    conns = db.query(DbConnection).filter(DbConnection.user_id == current_user.get("id")).all()
    results = []
    for c in conns:
        cr = _get_conn_creds(c)
        try:
            st = await MySQLClient.get_status(c.id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
            results.append({"id": c.id, "name": c.name, **st})
        except:
            results.append({"id": c.id, "name": c.name, "status": "error"})
    healthy = sum(1 for r in results if r.get("status") == "connected")
    return {"total": len(results), "healthy": healthy, "connections": results,
            "score": round(healthy/len(results)*100,1) if results else 100}

@router.get("/alerts")
async def get_alerts(level: Optional[str] = None, status: Optional[str] = None,
                     page=1, page_size=20, current_user=Depends(get_current_user),
                     db=Depends(get_db)):
    q = db.query(Alert).filter(Alert.user_id == current_user.get("id"))
    if level: q = q.filter(Alert.level == level)
    if status: q = q.filter(Alert.status == status)
    total = q.count()
    items = q.order_by(Alert.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "data": items}

@router.post("/alerts")
async def create_alert(alert_data: AlertCreate, current_user=Depends(get_current_user),
                       db=Depends(get_db)):
    alert = Alert(user_id=current_user.get("id"), connection_id=alert_data.connection_id,
        level=alert_data.level, title=alert_data.title, content=alert_data.content, status="unread")
    db.add(alert); db.commit(); db.refresh(alert)
    return alert

@router.put("/alerts/{aid}/read")
async def mark_read(aid: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id==aid, Alert.user_id==current_user.get("id")).first()
    if not alert: raise HTTPException(404,"not found")
    alert.status = "read"; db.commit()
    return {"message": "marked as read"}

@router.put("/alerts/{aid}/resolve")
async def resolve(aid: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id==aid, Alert.user_id==current_user.get("id")).first()
    if not alert: raise HTTPException(404,"not found")
    alert.status = "resolved"; db.commit()
    return {"message": "resolved"}

@router.get("/alerts/stats")
async def alert_stats(current_user=Depends(get_current_user), db=Depends(get_db)):
    uid = current_user.get("id")
    total = db.query(Alert).filter(Alert.user_id==uid).count()
    unread = db.query(Alert).filter(Alert.user_id==uid, Alert.status=="unread").count()
    critical = db.query(Alert).filter(Alert.user_id==uid, Alert.level=="critical", Alert.status=="unread").count()
    return {"total": total, "unread": unread, "critical": critical}
