"""MySQL Client v1.1 - Real metrics, slow query, capacity, schema"""
import aiomysql, ssl
from pymysql.cursors import DictCursor
from typing import Dict, Any, List
import time

class MySQLClient:
    _pool_cache: Dict[int, aiomysql.Pool] = {}

    @classmethod
    async def create_pool(cls, conn_id, host, port, user, pw, db,
                          max_conn=10, use_ssl=False):
        if conn_id in cls._pool_cache:
            return cls._pool_cache[conn_id]
        ctx = ssl.create_default_context() if use_ssl else None
        pool = await aiomysql.create_pool(
            host=host, port=port, user=user, pw=pw, db=db,
            charset="utf8mb4", cursorclass=DictCursor,
            minsize=1, maxsize=min(max_conn,20),
            ssl=ctx, connect_timeout=10, autocommit=True)
        cls._pool_cache[conn_id] = pool
        return pool

    @classmethod
    async def close_pool(cls, conn_id):
        if conn_id in cls._pool_cache:
            cls._pool_cache[conn_id].close()
            await cls._pool_cache[conn_id].wait_closed()
            del cls._pool_cache[conn_id]

    @classmethod
    async def close_all(cls):
        for cid in list(cls._pool_cache.keys()):
            await cls.close_pool(cid)

    @classmethod
    async def test_connection(cls, host, port, user, pw, db, use_ssl=False):
        start = time.time()
        try:
            ctx = ssl.create_default_context() if use_ssl else None
            conn = await aiomysql.connect(host=host, port=port, user=user,
                pw=pw, db=db, charset="utf8mb4", ssl=ctx, connect_timeout=8)
            async with conn.cursor(DictCursor) as cur:
                await cur.execute("SELECT VERSION() as v")
                row = await cur.fetchone()
                ver = row["v"] if row else "unknown"
            conn.close()
            return {"success": True, "version": ver, "latency_ms": int((time.time()-start)*1000)}
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": int((time.time()-start)*1000)}

    @classmethod
    async def execute(cls, conn_id, host, port, user, pw, database, sql,
                      max_conn=10, use_ssl=False):
        start = time.time()
        sq = sql.strip().upper()
        if sq.startswith(("SELECT","SHOW","DESCRIBE","EXPLAIN","WITH")): typ = "SELECT"
        elif sq.startswith("INSERT"): typ = "INSERT"
        elif sq.startswith("UPDATE"): typ = "UPDATE"
        elif sq.startswith("DELETE"): typ = "DELETE"
        else: typ = "DDL"
        pool = await cls.create_pool(conn_id, host, port, user, pw, database, max_conn, use_ssl)
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    if typ == "SELECT":
                        rows = await cur.fetchall()
                        cols = [d[0] for d in cur.description] if cur.description else []
                        res = {"type": "select", "columns": cols, "rows": [dict(r) for r in rows], "row_count": len(rows)}
                    else:
                        await conn.commit()
                        res = {"type": typ, "rows_affected": cur.rowcount, "last_insert_id": cur.lastrowid}
                    res["duration_ms"] = int((time.time()-start)*1000)
                    res["status"] = "success"
                    return res
        except Exception as e:
            return {"type": typ, "status": "error", "error": str(e), "duration_ms": int((time.time()-start)*1000)}

    @classmethod
    async def get_status(cls, conn_id, host, port, user, pw, database):
        pool = await cls.create_pool(conn_id, host, port, user, pw, database)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT VERSION() as v, @@global.max_conn as mc")
                info = await cur.fetchone()
                await cur.execute("SHOW STATUS LIKE 'Threads_connected'")
                tc = await cur.fetchone()
                await cur.execute("SHOW STATUS LIKE 'Queries'")
                q = await cur.fetchone()
                await cur.execute("SHOW STATUS LIKE 'Uptime'")
                up = await cur.fetchone()
                uptime = int(up["Value"]) if up else 1
                queries = int(q["Value"]) if q else 0
                await cur.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_pages_total'")
                bpt = await cur.fetchone()
                await cur.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_pages_free'")
                bpf = await cur.fetchone()
                total_pages = int(bpt["Value"]) if bpt else 1
                free_pages = int(bpf["Value"]) if bpf else 0
                buf_use = round((total_pages-free_pages)/total_pages*100, 1)
                return {"status": "connected", "version": info["v"], "uptime": uptime,
                    "connections": int(tc["Value"]) if tc else 0, "max_connections": int(info["mc"]),
                    "queries_per_second": round(queries/uptime,2), "buffer_usage": buf_use}

    @classmethod
    async def get_slow_queries(cls, conn_id, host, port, user, pw, database, limit=20):
        pool = await cls.create_pool(conn_id, host, port, user, pw, database)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO "
                    "FROM information_schema.PROCESSLIST WHERE COMMAND!='Sleep' AND TIME>1 "
                    "ORDER BY TIME DESC LIMIT %s", (limit,))
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    @classmethod
    async def get_capacity(cls, conn_id, host, port, user, pw, database):
        pool = await cls.create_pool(conn_id, host, port, user, pw, database)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT ROUND(SUM(data_length)/1024/1024,2) as dm, "
                    "ROUND(SUM(index_length)/1024/1024,2) as im, "
                    "ROUND(SUM(data_length+index_length)/1024/1024,2) as tm "
                    "FROM information_schema.TABLES WHERE table_schema=%s", (database,))
                sz = await cur.fetchone()
                await cur.execute("SELECT table_name, table_rows, "
                    "ROUND((data_length+index_length)/1024/1024,2) as smb "
                    "FROM information_schema.TABLES WHERE table_schema=%s "
                    "ORDER BY (data_length+index_length) DESC LIMIT 10", (database,))
                tbls = await cur.fetchall()
                return {"total_size_mb": float(sz["tm"] or 0), "data_size_mb": float(sz["dm"] or 0),
                    "index_size_mb": float(sz["im"] or 0), "tables": [dict(t) for t in tbls]}

    @classmethod
    async def get_schema(cls, conn_id, host, port, user, pw, database):
        pool = await cls.create_pool(conn_id, host, port, user, pw, database)
        lines = []
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SHOW TABLES")
                tbls = [list(r.values())[0] for r in await cur.fetchall()]
                for tbl in tbls:
                    await cur.execute(f"DESCRIBE `{tbl}`")
                    cols = await cur.fetchall()
                    cds = ", ".join(f"{c['Field']} {c['Type']}" for c in cols)
                    lines.append(f"Table `{tbl}` ({cds})")
        return "\n".join(lines)

mysql_client = MySQLClient()
