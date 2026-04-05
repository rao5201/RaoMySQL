"""MySQL 连接客户端服务"""
import pymysql, aiomysql, ssl
from pymysql.cursors import DictCursor
from typing import Dict, Any
import time, asyncio

class MySQLClient:
    """管理所有目标 MySQL 连接"""
    
    _pool_cache: Dict[int, aiomysql.Pool] = {}
    
    @classmethod
    async def create_pool(cls, conn_id: int, host: str, port: int, user: str,
                          password: str, database: str, max_connections: int = 10,
                          ssl_enabled: bool = False) -> aiomysql.Pool:
        """创建连接池（已存在则复用）"""
        if conn_id in cls._pool_cache:
            return cls._pool_cache[conn_id]
        
        ssl_context = None
        if ssl_enabled:
            ssl_context = ssl.create_default_context()
        
        pool = await aiomysql.create_pool(
            host=host, port=port, user=user, password=password,
            db=database, charset="utf8mb4", cursorclass=DictCursor,
            minsize=1, maxsize=min(max_connections, 20),
            ssl=ssl_context, connect_timeout=10,
            autocommit=True
        )
        cls._pool_cache[conn_id] = pool
        return pool
    
    @classmethod
    async def close_pool(cls, conn_id: int):
        if conn_id in cls._pool_cache:
            cls._pool_cache[conn_id].close()
            await cls._pool_cache[conn_id].wait_closed()
            del cls._pool_cache[conn_id]
    
    @classmethod
    async def close_all(cls):
        for cid in list(cls._pool_cache.keys()):
            await cls.close_pool(cid)
    
    @classmethod
    async def execute(cls, conn_id: int, host: str, port: int,
                      user: str, password: str, database: str,
                      sql: str, max_connections: int = 10,
                      ssl_enabled: bool = False) -> Dict[str, Any]:
        """执行 SQL，返回统一结果"""
        start = time.time()
        sql_upper = sql.strip().upper()
        
        # 判断 SQL 类型
        if any(sql_upper.startswith(k) for k in ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH")):
            sql_type = "SELECT"
        elif sql_upper.startswith("INSERT"):
            sql_type = "INSERT"
        elif sql_upper.startswith("UPDATE"):
            sql_type = "UPDATE"
        elif sql_upper.startswith("DELETE"):
            sql_type = "DELETE"
        else:
            sql_type = "DDL"
        
        pool = await cls.create_pool(conn_id, host, port, user, password, database, max_connections, ssl_enabled)
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    
                    if sql_type == "SELECT":
                        rows = await cur.fetchall()
                        columns = [desc[0] for desc in cur.description] if cur.description else []
                        result = {
                            "type": "select",
                            "columns": columns,
                            "rows": [dict(r) for r in rows],
                            "row_count": len(rows)
                        }
                    else:
                        # DDL/INSERT/UPDATE/DELETE 需要手动 commit
                        await conn.commit()
                        result = {
                            "type": sql_type,
                            "rows_affected": cur.rowcount,
                            "last_insert_id": cur.lastrowid
                        }
                    
                    result["duration_ms"] = int((time.time() - start) * 1000)
                    result["status"] = "success"
                    return result
                    
        except Exception as e:
            return {
                "type": sql_type,
                "status": "error",
                "error": str(e),
                "duration_ms": int((time.time() - start) * 1000)
            }

mysql_client = MySQLClient()
