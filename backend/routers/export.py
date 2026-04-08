"""RaoMySQL Export Router - CSV/JSON data export"""
import csv, io, json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database.init_db import get_db
from backend.database.models import DbConnection
from backend.routers.auth import get_current_user
from backend.utils.crypto import decrypt_password
from backend.services.mysql_client import MySQLClient

router = APIRouter(prefix="/api/export", tags=["Export"])

def _get_conn(conn_id, user_id, db):
    return db.query(DbConnection).filter(
        DbConnection.id == conn_id, DbConnection.user_id == user_id).first()

def _creds(conn):
    pw = decrypt_password(conn.password_enc) if conn.password_enc else ""
    return {"host": conn.host, "port": conn.port, "user": conn.username,
            "pw": pw, "database": conn.database}

@router.get("/csv")
async def export_csv(
    connection_id: int, table: str,
    columns: Optional[str] = None,
    where: Optional[str] = None,
    limit: int = Query(default=10000, le=100000),
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """Export table data as CSV"""
    conn = _get_conn(connection_id, current_user.get("id"), db)
    if not conn: raise HTTPException(404, "connection not found")
    cr = _creds(conn)
    pool = await MySQLClient.create_pool(
        connection_id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
    try:
        async with pool.acquire() as c:
            async with c.cursor() as cur:
                cols = columns if columns else "*"
                sql = f"SELECT {cols} FROM `{table}`"
                if where: sql += f" WHERE {where}"
                sql += f" LIMIT {limit}"
                await cur.execute(sql)
                rows = await cur.fetchall()
                col_names = [d[0] for d in cur.description] if cur.description else []
    except Exception as e:
        raise HTTPException(400, str(e))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(col_names)
    for row in rows:
        writer.writerow([str(v) if v is not None else "" for v in row])
    output.seek(0)
    fname = f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(output, media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fname}"})

@router.get("/json")
async def export_json(
    connection_id: int, table: str,
    columns: Optional[str] = None,
    where: Optional[str] = None,
    limit: int = Query(default=10000, le=100000),
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """Export table data as JSON"""
    conn = _get_conn(connection_id, current_user.get("id"), db)
    if not conn: raise HTTPException(404, "connection not found")
    cr = _creds(conn)
    pool = await MySQLClient.create_pool(
        connection_id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
    try:
        async with pool.acquire() as c:
            async with c.cursor() as cur:
                cols = columns if columns else "*"
                sql = f"SELECT {cols} FROM `{table}`"
                if where: sql += f" WHERE {where}"
                sql += f" LIMIT {limit}"
                await cur.execute(sql)
                rows = await cur.fetchall()
    except Exception as e:
        raise HTTPException(400, str(e))

    data = [dict(r) for r in rows]
    # Convert non-serializable types
    for row in data:
        for k, v in row.items():
            if hasattr(v, 'isoformat'): row[k] = v.isoformat()
            elif not isinstance(v, (str, int, float, bool, type(None))):
                row[k] = str(v)

    fname = f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(
        io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2, default=str).encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={fname}"})

@router.get("/tables")
async def list_tables(
    connection_id: int,
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """List all tables in a connection"""
    conn = _get_conn(connection_id, current_user.get("id"), db)
    if not conn: raise HTTPException(404, "connection not found")
    cr = _creds(conn)
    pool = await MySQLClient.create_pool(
        connection_id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
    async with pool.acquire() as c:
        async with c.cursor() as cur:
            await cur.execute("SHOW TABLES")
            tables = [list(r.values())[0] for r in await cur.fetchall()]
    return {"tables": tables}

@router.get("/count")
async def table_count(
    connection_id: int, table: str,
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """Get row count for a table"""
    conn = _get_conn(connection_id, current_user.get("id"), db)
    if not conn: raise HTTPException(404, "connection not found")
    cr = _creds(conn)
    pool = await MySQLClient.create_pool(
        connection_id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
    async with pool.acquire() as c:
        async with c.cursor() as cur:
            await cur.execute(f"SELECT COUNT(*) as cnt FROM `{table}`")
            row = await cur.fetchone()
            return {"table": table, "count": row["cnt"]}
