"""RaoMySQL Export Router v1.2 - Async DB + current_user.id Fix"""
import csv, io, json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.init_db import get_db
from backend.database.models import DbConnection, User
from .auth import get_current_user
from backend.utils.crypto import decrypt_password
from backend.services.mysql_client import MySQLClient

router = APIRouter(prefix="/api/export", tags=["Export"])

async def _get_conn_creds(conn_id: int, user: User, db: AsyncSession):
    """验证连接归属，返回凭证"""
    result = await db.execute(select(DbConnection).where(
        DbConnection.id == conn_id,
        DbConnection.user_id == user.id
    ))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="connection not found")
    pw = decrypt_password(conn.password_enc) if conn.password_enc else ""
    return conn, {"host": conn.host, "port": conn.port,
                  "user": conn.username, "pw": pw, "database": conn.database_name}

async def _run_query(conn_id: int, creds: dict, sql: str):
    pool = await MySQLClient.create_pool(
        conn_id, creds["host"], creds["port"],
        creds["user"], creds["pw"], creds["database"])
    async with pool.acquire() as c:
        async with c.cursor() as cur:
            await cur.execute(sql)
            rows = await cur.fetchall()
            col_names = [d[0] for d in cur.description] if cur.description else []
            return col_names, rows

@router.get("/csv")
async def export_csv(
    connection_id: int, table: str,
    columns: Optional[str] = None,
    where: Optional[str] = None,
    limit: int = Query(default=10000, le=100000),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export table data as CSV"""
    _, cr = await _get_conn_creds(connection_id, current, db)
    cols = columns if columns else "*"
    safe_table = table.replace("`", "").replace(";", "").replace("--", "")
    sql = f"SELECT {cols} FROM `{safe_table}`"
    if where: sql += f" WHERE {where}"
    sql += f" LIMIT {limit}"
    try:
        col_names, rows = await _run_query(connection_id, cr, sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(col_names)
    for row in rows:
        writer.writerow([str(v) if v is not None else "" for v in row])
    output.seek(0)
    fname = f"{safe_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(output, media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fname}"})

@router.get("/json")
async def export_json(
    connection_id: int, table: str,
    columns: Optional[str] = None,
    where: Optional[str] = None,
    limit: int = Query(default=10000, le=100000),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export table data as JSON"""
    _, cr = await _get_conn_creds(connection_id, current, db)
    cols = columns if columns else "*"
    safe_table = table.replace("`", "").replace(";", "").replace("--", "")
    sql = f"SELECT {cols} FROM `{safe_table}`"
    if where: sql += f" WHERE {where}"
    sql += f" LIMIT {limit}"
    try:
        _, rows = await _run_query(connection_id, cr, sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    data = [dict(r) for r in rows]
    for row in data:
        for k, v in row.items():
            if hasattr(v, 'isoformat'): row[k] = v.isoformat()
            elif not isinstance(v, (str, int, float, bool, type(None))):
                row[k] = str(v)

    fname = f"{safe_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(
        io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2, default=str).encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={fname}"})

@router.get("/tables")
async def list_tables(
    connection_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all tables in a connection"""
    _, cr = await _get_conn_creds(connection_id, current, db)
    try:
        _, rows = await _run_query(connection_id, cr, "SHOW TABLES")
        tables = [list(r.values())[0] for r in rows]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"tables": tables}

@router.get("/count")
async def table_count(
    connection_id: int, table: str,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get row count for a table"""
    _, cr = await _get_conn_creds(connection_id, current, db)
    safe_table = table.replace("`", "").replace(";", "")
    try:
        _, rows = await _run_query(connection_id, cr, f"SELECT COUNT(*) as cnt FROM `{safe_table}`")
        row = rows[0] if rows else {}
        return {"table": table, "count": row.get("cnt", 0) if isinstance(row, dict) else row[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
