"""
RaoMySQL - 监控告警路由
数据库状态监控和告警管理
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from backend.database.init_db import get_db
from backend.database.models import DbConnection, Alert
from backend.routers.auth import get_current_user
import random

router = APIRouter(prefix="/api/monitor", tags=["监控告警"])


class MonitorStats(BaseModel):
    connection_id: int
    status: str
    version: Optional[str] = None
    uptime: Optional[int] = None
    connections: int
    max_connections: int
    queries_per_second: float
    buffer_usage: float
    created_at: datetime


class AlertCreate(BaseModel):
    connection_id: Optional[int] = None
    level: str
    title: str
    content: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    user_id: int
    connection_id: Optional[int]
    level: str
    title: str
    content: Optional[str]
    status: str
    created_at: datetime


@router.get("/{connection_id}/status")
async def get_connection_status(
    connection_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据库连接状态"""
    conn = db.query(DbConnection).filter(
        DbConnection.id == connection_id,
        DbConnection.user_id == current_user.get("id")
    ).first()
    if not conn:
        return {"status": "disconnected", "error": "连接不存在"}
    
    # TODO: 实际连接数据库获取状态
    # 这里返回模拟数据
    return {
        "connection_id": connection_id,
        "status": "connected",
        "version": "8.0.35",
        "uptime": 86400 * random.randint(1, 30),
        "connections": random.randint(10, 50),
        "max_connections": conn.max_connections or 100,
        "queries_per_second": round(random.uniform(100, 1000), 2),
        "buffer_usage": round(random.uniform(30, 80), 2),
        "checked_at": datetime.now().isoformat()
    }


@router.get("/{connection_id}/slow-queries")
async def get_slow_queries(
    connection_id: int,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取慢查询列表"""
    # TODO: 从数据库获取慢查询
    return {
        "connection_id": connection_id,
        "queries": [],
        "total": 0
    }


@router.get("/{connection_id}/capacity")
async def get_capacity(
    connection_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取容量分析"""
    # TODO: 实际查询数据库容量
    return {
        "connection_id": connection_id,
        "total_size_mb": round(random.uniform(100, 5000), 2),
        "data_size_mb": round(random.uniform(80, 4000), 2),
        "index_size_mb": round(random.uniform(20, 1000), 2),
        "tables": [
            {"name": "users", "size_mb": round(random.uniform(10, 500), 2), "rows": random.randint(1000, 100000)},
            {"name": "orders", "size_mb": round(random.uniform(10, 500), 2), "rows": random.randint(1000, 100000)},
            {"name": "products", "size_mb": round(random.uniform(5, 200), 2), "rows": random.randint(500, 50000)},
        ]
    }


@router.get("/health")
async def get_overall_health(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取整体健康状态"""
    connections = db.query(DbConnection).filter(
        DbConnection.user_id == current_user.get("id")
    ).all()
    
    total = len(connections)
    healthy = random.randint(total - 2, total) if total > 0 else 0
    warning = random.randint(0, 2)
    critical = max(0, total - healthy - warning)
    
    return {
        "total_connections": total,
        "healthy": healthy,
        "warning": warning,
        "critical": critical,
        "score": round((healthy / total * 100) if total > 0 else 100, 1),
        "last_checked": datetime.now().isoformat()
    }


# ==================== 告警相关 ====================

@router.get("/alerts")
async def get_alerts(
    level: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取告警列表"""
    query = db.query(Alert).filter(Alert.user_id == current_user.get("id"))
    
    if level:
        query = query.filter(Alert.level == level)
    if status:
        query = query.filter(Alert.status == status)
    
    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return {"total": total, "data": alerts}


@router.post("/alerts")
async def create_alert(
    alert_data: AlertCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建告警（测试用）"""
    alert = Alert(
        user_id=current_user.get("id"),
        connection_id=alert_data.connection_id,
        level=alert_data.level,
        title=alert_data.title,
        content=alert_data.content,
        status="unread"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记告警已读"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.get("id")
    ).first()
    if not alert:
        return {"error": "告警不存在"}
    alert.status = "read"
    db.commit()
    return {"message": "已标记为已读"}


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """解决告警"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.get("id")
    ).first()
    if not alert:
        return {"error": "告警不存在"}
    alert.status = "resolved"
    db.commit()
    return {"message": "已标记为已解决"}


@router.get("/alerts/stats")
async def get_alert_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取告警统计"""
    total = db.query(Alert).filter(Alert.user_id == current_user.get("id")).count()
    unread = db.query(Alert).filter(
        Alert.user_id == current_user.get("id"),
        Alert.status == "unread"
    ).count()
    critical = db.query(Alert).filter(
        Alert.user_id == current_user.get("id"),
        Alert.level == "critical",
        Alert.status == "unread"
    ).count()
    warning = db.query(Alert).filter(
        Alert.user_id == current_user.get("id"),
        Alert.level == "warning",
        Alert.status == "unread"
    ).count()
    
    return {
        "total": total,
        "unread": unread,
        "critical": critical,
        "warning": warning
    }