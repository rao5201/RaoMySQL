"""数据库连接管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from backend.database.init_db import get_db
from backend.database.models import DbConnection, User
from .auth import get_current_user
from backend.services.mysql_client import mysql_client
from backend.utils.crypto import encrypt_password, decrypt_password

router = APIRouter(prefix="/api/connections", tags=["数据库连接"])

class ConnCreate(BaseModel):
    name: str
    host: str
    port: int = 3306
    username: str
    password: str
    database_name: str
    tags: Optional[str] = ""
    ssl_enabled: bool = False
    max_connections: int = 100

class ConnUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_name: Optional[str] = None
    tags: Optional[str] = None
    ssl_enabled: Optional[bool] = None
    max_connections: Optional[int] = None

class ConnOut(BaseModel):
    id: int
    name: str
    host: str
    port: int
    username: str
    password_enc: str
    database_name: str
    tags: str
    ssl_enabled: bool
    max_connections: int
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[ConnOut])
async def list_connections(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(DbConnection)
    if current.role != "admin":
        q = q.where(DbConnection.user_id == current.id)
    result = await db.execute(q)
    conns = result.scalars().all()
    return [ConnOut(
        id=c.id, name=c.name, host=c.host, port=c.port,
        username=c.username or "", password_enc=c.password_enc or "",
        database_name=c.database_name or "", tags=c.tags or "",
        ssl_enabled=c.ssl_enabled, max_connections=c.max_connections,
        created_at=str(c.created_at)
    ) for c in conns]

@router.post("")
async def create_connection(data: ConnCreate, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conn = DbConnection(
        user_id=current.id,
        name=data.name, host=data.host, port=data.port,
        username=data.username,
        password_enc=encrypt_password(data.password),
        database_name=data.database_name,
        tags=data.tags, ssl_enabled=data.ssl_enabled,
        max_connections=data.max_connections
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return {"id": conn.id, "name": conn.name, "status": "created"}

@router.put("/{conn_id}")
async def update_connection(conn_id: int, data: ConnUpdate, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")
    if current.role != "admin" and conn.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "password" and value:
            setattr(conn, "password_enc", encrypt_password(value))
        elif field == "password":
            pass
        else:
            setattr(conn, field, value)
    await db.commit()
    return {"status": "updated"}

@router.delete("/{conn_id}")
async def delete_connection(conn_id: int, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")
    if current.role != "admin" and conn.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")
    await mysql_client.close_pool(conn_id)
    await db.delete(conn)
    await db.commit()
    return {"status": "deleted"}

@router.post("/{conn_id}/test")
async def test_connection(conn_id: int, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")
    if current.role != "admin" and conn.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")
    
    password = decrypt_password(conn.password_enc)
    try:
        result = await mysql_client.execute(
            conn.id, conn.host, conn.port, conn.username, password,
            conn.database_name, sql="SELECT 1", max_connections=conn.max_connections,
            ssl_enabled=conn.ssl_enabled
        )
        if result.get("status") == "success":
            return {"status": "ok", "message": "连接成功"}
        else:
            return {"status": "error", "message": result.get("error", "连接失败")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/{conn_id}/schema")
async def get_schema(conn_id: int, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")
    if current.role != "admin" and conn.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")
    
    password = decrypt_password(conn.password_enc)
    try:
        # 获取所有表
        tables_res = await mysql_client.execute(
            conn.id, conn.host, conn.port, conn.username, password,
            conn.database_name, sql=f"SHOW TABLES FROM `{conn.database_name}`",
            ssl_enabled=conn.ssl_enabled
        )
        tables = [list(r.values())[0] for r in tables_res.get("rows", [])]
        
        schema = {}
        for table in tables:
            cols_res = await mysql_client.execute(
                conn.id, conn.host, conn.port, conn.username, password,
                conn.database_name,
                sql=f"DESCRIBE `{table}`",
                ssl_enabled=conn.ssl_enabled
            )
            schema[table] = cols_res.get("rows", [])
        
        return {"connection_id": conn_id, "database": conn.database_name, "tables": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
