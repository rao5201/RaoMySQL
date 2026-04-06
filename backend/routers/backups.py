"""
RaoMySQL - 备份恢复路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.database.init_db import get_db
from backend.database.models import Backup
from backend.routers.auth import get_current_user
import os

router = APIRouter(prefix="/api/backups", tags=["备份恢复"])


class BackupCreate(BaseModel):
    connection_id: int
    database: str
    backup_name: Optional[str] = None


class BackupResponse(BaseModel):
    id: int
    connection_id: int
    file_path: Optional[str]
    file_size: Optional[int]
    status: str
    backup_type: str
    checksum: Optional[str]


@router.get("")
async def get_backups(
    connection_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取备份列表"""
    query = db.query(Backup).filter(Backup.user_id == current_user.get("id"))
    if connection_id:
        query = query.filter(Backup.connection_id == connection_id)
    total = query.count()
    backups = query.order_by(Backup.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "page": page, "data": backups}


@router.post("")
async def create_backup(
    backup_data: BackupCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建备份任务"""
    from backend.database.models import DbConnection
    conn = db.query(DbConnection).filter(
        DbConnection.id == backup_data.connection_id,
        DbConnection.user_id == current_user.get("id")
    ).first()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")
    
    backup = Backup(
        connection_id=backup_data.connection_id,
        user_id=current_user.get("id"),
        backup_type="manual",
        status="pending"
    )
    db.add(backup)
    db.commit()
    return {"id": backup.id, "status": "pending", "message": "备份任务已创建"}


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除备份"""
    backup = db.query(Backup).filter(
        Backup.id == backup_id,
        Backup.user_id == current_user.get("id")
    ).first()
    if not backup:
        raise HTTPException(status_code=404, detail="备份不存在")
    if backup.file_path and os.path.exists(backup.file_path):
        os.remove(backup.file_path)
    db.delete(backup)
    db.commit()
    return {"message": "删除成功"}