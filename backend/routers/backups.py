"""RaoMySQL Backup Router v1.1 - Real mysqldump execution"""
import os, hashlib, asyncio, shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database.init_db import get_db
from backend.database.models import Backup, DbConnection
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

def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _tool_ok(name):
    return shutil.which(name) is not None

async def _run_backup(bid, cid, dbname):
    from backend.database.init_db import SessionLocal
    from backend.database.models import DbConnection
    db = SessionLocal()
    bk = db.query(Backup).filter(Backup.id == bid).first()
    if not bk: db.close(); return
    conn = db.query(DbConnection).filter(DbConnection.id == cid).first()
    if not conn: db.close(); return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{dbname}_{ts}.sql"
    fpath = os.path.join(BACKUP_DIR, fname)
    try:
        plain = decrypt_password(conn.password_enc) if conn.password_enc else ""
        cmd = ["mysqldump", "-h", conn.host, "-P", str(conn.port),
               "-u", conn.username, f"-p{plain}",
               "--single-transaction", "--routines", "--triggers",
               "--set-gtid-purged=OFF", dbname]
        bk.status = "running"; db.commit()
        with open(fpath, "w", encoding="utf-8") as f:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=f,
                stderr=asyncio.subprocess.PIPE)
            _, stderr = await proc.communicate()
        if proc.returncode != 0:
            bk.status = "failed"; db.commit()
            if os.path.exists(fpath): os.remove(fpath)
            db.close(); return
        bk.file_path = fpath
        bk.file_size = os.path.getsize(fpath)
        bk.checksum = _sha256(fpath)
        bk.status = "success"; db.commit()
    except: bk.status = "failed"; db.commit()
    finally: db.close()

async def _run_restore(fpath, conn, dbname):
    plain = decrypt_password(conn.password_enc) if conn.password_enc else ""
    cmd = ["mysql", "-h", conn.host, "-P", str(conn.port),
           "-u", conn.username, f"-p{plain}", dbname]
    with open(fpath, "r", encoding="utf-8") as f:
        proc = await asyncio.create_subprocess_exec(*cmd, stdin=f,
            stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode("utf-8", errors="ignore") or "restore failed")

@router.get("")
async def get_backups(connection_id: Optional[int] = None, page=1, page_size=20,
                      current_user=Depends(get_current_user), db=Depends(get_db)):
    q = db.query(Backup).filter(Backup.user_id==current_user.get("id"))
    if connection_id: q = q.filter(Backup.connection_id==connection_id)
    total = q.count()
    items = q.order_by(Backup.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total":total,"page":page,"data":items}

@router.post("")
async def create_backup(data:BackupCreate, bt=BackgroundTasks(),
                        current_user=Depends(get_current_user), db=Depends(get_db)):
    if not _tool_ok("mysqldump"): raise HTTPException(503,"mysqldump not found")
    conn = db.query(DbConnection).filter(
        DbConnection.id==data.connection_id,
        DbConnection.user_id==current_user.get("id")).first()
    if not conn: raise HTTPException(404,"connection not found")
    bk = Backup(connection_id=data.connection_id, user_id=current_user.get("id"),
                backup_type="manual", status="pending")
    db.add(bk); db.commit(); db.refresh(bk)
    bt.add_task(_run_backup, bk.id, conn.id, data.database)
    return {"id":bk.id,"status":"pending","message":"backup started"}

@router.post("/{bid}/restore")
async def restore_backup(bid:int, data:RestoreRequest,
                         current_user=Depends(get_current_user), db=Depends(get_db)):
    if not _tool_ok("mysql"): raise HTTPException(503,"mysql not found")
    bk = db.query(Backup).filter(Backup.id==bid,
        Backup.user_id==current_user.get("id")).first()
    if not bk or bk.status!="success": raise HTTPException(400,"backup not ready")
    if not bk.file_path or not os.path.exists(bk.file_path): raise HTTPException(404,"file not found")
    if bk.checksum and _sha256(bk.file_path)!=bk.checksum: raise HTTPException(400,"checksum mismatch")
    conn = db.query(DbConnection).filter(
        DbConnection.id==data.connection_id,
        DbConnection.user_id==current_user.get("id")).first()
    if not conn: raise HTTPException(404,"connection not found")
    try:
        await _run_restore(bk.file_path, conn, data.database)
        return {"message":f"restored to {data.database}"}
    except RuntimeError as e: raise HTTPException(500,str(e))

@router.get("/{bid}/download")
async def download_backup(bid:int, current_user=Depends(get_current_user),
                          db=Depends(get_db)):
    bk = db.query(Backup).filter(Backup.id==bid,
        Backup.user_id==current_user.get("id")).first()
    if not bk or not bk.file_path or not os.path.exists(bk.file_path):
        raise HTTPException(404,"file not found")
    return FileResponse(path=bk.file_path, filename=os.path.basename(bk.file_path),
                       media_type="application/octet-stream")

@router.delete("/{bid}")
async def delete_backup(bid:int, current_user=Depends(get_current_user),
                       db=Depends(get_db)):
    bk = db.query(Backup).filter(Backup.id==bid,
        Backup.user_id==current_user.get("id")).first()
    if not bk: raise HTTPException(404,"not found")
    if bk.file_path and os.path.exists(bk.file_path): os.remove(bk.file_path)
    db.delete(bk); db.commit()
    return {"message":"deleted"}

@router.get("/check-tools")
async def check_tools(current_user=Depends(get_current_user)):
    return {"mysqldump":_tool_ok("mysqldump"),"mysql":_tool_ok("mysql"),"backup_dir":BACKUP_DIR}
