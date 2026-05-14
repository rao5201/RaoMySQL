"""RaoMySQL Backup Router v1.2 - Async DB + Security Fixes"""
import os, hashlib, asyncio, shutil, re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from backend.database.init_db import get_db
from backend.database.models import Backup, DbConnection, User
from .auth import get_current_user
from backend.utils.crypto import decrypt_password

router = APIRouter(prefix="/api/backups", tags=["Backup"])
BACKUP_DIR = os.path.join("data", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

class BackupCreate(BaseModel):
    connection_id: int
    database: str

class RestoreRequest(BaseModel):
    connection_id: int
    database: str

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _tool_ok(name: str) -> bool:
    return shutil.which(name) is not None

def _safe_db_name(name: str) -> str:
    """只允许字母数字下划线，防止 SQL 注入"""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise HTTPException(status_code=400, detail="无效的数据库名称")
    return name

async def _run_backup(bid: int, cid: int, dbname: str):
    from backend.database.init_db import async_session
    from backend.database.models import Backup, DbConnection
    db = async_session()
    async with db:
        bk = (await db.execute(select(Backup).where(Backup.id == bid))).scalar_one_or_none()
        if not bk: return
        conn = (await db.execute(select(DbConnection).where(DbConnection.id == cid))).scalar_one_or_none()
        if not conn: return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = _safe_db_name(dbname)
        fname = f"{safe_name}_{ts}.sql"
        fpath = os.path.join(BACKUP_DIR, fname)
        try:
            plain = decrypt_password(conn.password_enc) if conn.password_enc else ""
            cmd = ["mysqldump", "-h", conn.host, "-P", str(conn.port),
                   "-u", conn.username, f"-p{plain}",
                   "--single-transaction", "--routines", "--triggers",
                   "--set-gtid-purged=OFF", safe_name]
            bk.status = "running"; await db.commit()
            with open(fpath, "w", encoding="utf-8") as f:
                proc = await asyncio.create_subprocess_exec(*cmd, stdout=f,
                    stderr=asyncio.subprocess.PIPE)
                _, stderr = await proc.communicate()
            if proc.returncode != 0:
                bk.status = "failed"; await db.commit()
                if os.path.exists(fpath): os.remove(fpath)
                return
            bk.file_path = fpath
            bk.file_size = os.path.getsize(fpath)
            bk.checksum = _sha256(fpath)
            bk.status = "success"; await db.commit()
        except: bk.status = "failed"; await db.commit()

async def _run_restore(fpath: str, conn: DbConnection, dbname: str):
    plain = decrypt_password(conn.password_enc) if conn.password_enc else ""
    cmd = ["mysql", "-h", conn.host, "-P", str(conn.port),
           "-u", conn.username, f"-p{plain}", _safe_db_name(dbname)]
    with open(fpath, "r", encoding="utf-8") as f:
        proc = await asyncio.create_subprocess_exec(*cmd, stdin=f,
            stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode("utf-8", errors="ignore") or "restore failed")

@router.get("")
async def get_backups(connection_id: Optional[int] = None, page: int = 1, page_size: int = 20,
                       current: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    q = select(Backup).where(Backup.user_id == current.id)
    if connection_id: q = q.where(Backup.connection_id == connection_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    items = (await db.execute(
        q.order_by(Backup.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    )).scalars().all()
    return {"total": total, "page": page, "data": items}

@router.post("")
async def create_backup(data: BackupCreate, bt=BackgroundTasks(),
                        current: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    if not _tool_ok("mysqldump"): raise HTTPException(503, "mysqldump not found")
    result = await db.execute(select(DbConnection).where(
        DbConnection.id == data.connection_id, DbConnection.user_id == current.id))
    conn = result.scalar_one_or_none()
    if not conn: raise HTTPException(404, "connection not found")
    bk = Backup(connection_id=data.connection_id, user_id=current.id,
                 backup_type="manual", status="pending")
    db.add(bk); await db.commit(); await db.refresh(bk)
    bt.add_task(_run_backup, bk.id, conn.id, data.database)
    return {"id": bk.id, "status": "pending", "message": "backup started"}

@router.post("/{bid}/restore")
async def restore_backup(bid: int, data: RestoreRequest,
                        current: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    if not _tool_ok("mysql"): raise HTTPException(503, "mysql not found")
    bk_result = await db.execute(select(Backup).where(
        Backup.id == bid, Backup.user_id == current.id))
    bk = bk_result.scalar_one_or_none()
    if not bk or bk.status != "success": raise HTTPException(400, "backup not ready")
    if not bk.file_path or not os.path.exists(bk.file_path): raise HTTPException(404, "file not found")
    # 路径安全：只允许备份目录内的文件（防止 ../ 路径遍历）
    real_path = os.path.realpath(bk.file_path)
    real_backup_dir = os.path.realpath(BACKUP_DIR)
    if not real_path.startswith(real_backup_dir):
        raise HTTPException(400, "非法文件路径")
    conn_result = await db.execute(select(DbConnection).where(
        DbConnection.id == data.connection_id, DbConnection.user_id == current.id))
    conn = conn_result.scalar_one_or_none()
    if not conn: raise HTTPException(404, "connection not found")
    try:
        await _run_restore(bk.file_path, conn, data.database)
        return {"message": f"restored to {data.database}"}
    except RuntimeError as e: raise HTTPException(500, str(e))

@router.get("/{bid}/download")
async def download_backup(bid: int, current: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Backup).where(
        Backup.id == bid, Backup.user_id == current.id))
    bk = result.scalar_one_or_none()
    if not bk or not bk.file_path or not os.path.exists(bk.file_path):
        raise HTTPException(404, "file not found")
    return FileResponse(path=bk.file_path, filename=os.path.basename(bk.file_path),
                        media_type="application/octet-stream")

@router.delete("/{bid}")
async def delete_backup(bid: int, current: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Backup).where(
        Backup.id == bid, Backup.user_id == current.id))
    bk = result.scalar_one_or_none()
    if not bk: raise HTTPException(404, "not found")
    if bk.file_path and os.path.exists(bk.file_path): os.remove(bk.file_path)
    await db.delete(bk); await db.commit()
    return {"message": "deleted"}

@router.get("/check-tools")
async def check_tools(current: User = Depends(get_current_user)):
    return {"mysqldump": _tool_ok("mysqldump"), "mysql": _tool_ok("mysql"), "backup_dir": BACKUP_DIR}
