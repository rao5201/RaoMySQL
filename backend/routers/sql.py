"""SQL 执行路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from database.init_db import get_db
from database.models import DbConnection, SqlHistory, SqlSnippet, User
from routers.auth import get_current_user
from services.mysql_client import mysql_client
from utils.crypto import decrypt_password

router = APIRouter(prefix="/api/query", tags=["SQL执行"])

class QueryRequest(BaseModel):
    connection_id: int
    sql: str
    limit: int = 100

class SnippetCreate(BaseModel):
    name: str
    sql_text: str
    description: Optional[str] = None

@router.post("")
async def execute_sql(req: QueryRequest, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbConnection).where(DbConnection.id == req.connection_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")
    if current.role != "admin" and conn.user_id != current.id:
        raise HTTPException(status_code=403, detail="无权限")
    
    password = decrypt_password(conn.password_enc)
    sql = req.sql.strip()
    
    # viewer 角色只能执行 SELECT
    if current.role == "viewer" and not sql.upper().startswith("SELECT"):
        raise HTTPException(status_code=403, detail="只读用户只能执行 SELECT 查询")
    
    # 执行
    exec_result = await mysql_client.execute(
        conn.id, conn.host, conn.port, conn.username, password,
        conn.database_name, sql=sql, max_connections=conn.max_connections,
        ssl_enabled=conn.ssl_enabled
    )
    
    # 记录历史
    history = SqlHistory(
        user_id=current.id, connection_id=conn.id,
        sql_text=sql, sql_type=exec_result.get("type"),
        duration_ms=exec_result.get("duration_ms"),
        rows_affected=exec_result.get("rows_affected"),
        status=exec_result.get("status"),
        error_msg=exec_result.get("error")
    )
    db.add(history)
    await db.commit()
    
    return exec_result

@router.get("/history")
async def query_history(connection_id: Optional[int] = None, limit: int = 50,
                        current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(SqlHistory).where(SqlHistory.user_id == current.id)
    if connection_id:
        q = q.where(SqlHistory.connection_id == connection_id)
    q = q.order_by(SqlHistory.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return [
        {
            "id": h.id, "sql_text": h.sql_text, "sql_type": h.sql_type,
            "duration_ms": h.duration_ms, "rows_affected": h.rows_affected,
            "status": h.status, "error_msg": h.error_msg,
            "created_at": str(h.created_at)
        }
        for h in result.scalars().all()
    ]

@router.post("/snippets")
async def create_snippet(data: SnippetCreate, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    snippet = SqlSnippet(user_id=current.id, name=data.name, sql_text=data.sql_text, description=data.description)
    db.add(snippet)
    await db.commit()
    return {"id": snippet.id, "name": snippet.name}

@router.get("/snippets")
async def list_snippets(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SqlSnippet).where(SqlSnippet.user_id == current.id).order_by(SqlSnippet.created_at.desc()))
    return [{"id": s.id, "name": s.name, "sql_text": s.sql_text, "description": s.description} for s in result.scalars().all()]

@router.delete("/snippets/{snippet_id}")
async def delete_snippet(snippet_id: int, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SqlSnippet).where(SqlSnippet.id == snippet_id, SqlSnippet.user_id == current.id))
    snippet = result.scalar_one_or_none()
    if not snippet:
        raise HTTPException(status_code=404, detail="片段不存在")
    await db.delete(snippet)
    await db.commit()
    return {"status": "deleted"}
