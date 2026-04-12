"""RaoMySQL AI Router v1.2 - Secure LLM support (OpenAI/Ollama)"""
import os, json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from backend.database.init_db import get_db
from backend.database.models import DbConnection, User
from .auth import get_current_user
from backend.services.mysql_client import MySQLClient
from backend.config import settings

router = APIRouter(prefix="/api/ai", tags=["AI"])

class NL2SQLRequest(BaseModel):
    question: str
    connection_id: int

class AnalyzeSlowRequest(BaseModel):
    sql: str
    connection_id: Optional[int] = None

class ChatRequest(BaseModel):
    message: str
    connection_id: Optional[int] = None

class AIConfigModel(BaseModel):
    provider: str = "openai"
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    model: str = "gpt-4"

def _get_provider() -> str:
    return os.getenv("AI_PROVIDER", "openai")

def _get_model() -> str:
    return os.getenv("AI_MODEL", "gpt-4o")

def _get_endpoint() -> str:
    return os.getenv("AI_ENDPOINT", "")

def _get_key() -> str:
    return os.getenv("OPENAI_API_KEY", "")

def _get_conn_creds(conn: DbConnection) -> dict:
    from backend.utils.crypto import decrypt_password
    pw = decrypt_password(conn.password_enc) if conn.password_enc else ""
    return {
        "host": conn.host, "port": conn.port,
        "user": conn.username, "pw": pw,
        "database": conn.database_name
    }

def _check_conn_ownership(conn: DbConnection, user: User) -> None:
    """验证连接归属（admin 可访问所有连接）"""
    if user.role != "admin" and conn.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权限访问此连接")

async def _call_llm(prompt: str, system: str = "You are a helpful database assistant."):
    import httpx
    provider = _get_provider()
    model = _get_model()
    if provider == "ollama":
        ep = _get_endpoint() or "http://localhost:11434"
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{ep}/api/chat", json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ]
            })
            r.raise_for_status()
            return r.json()["message"]["content"]
    else:
        key = _get_key()
        if not key:
            raise HTTPException(status_code=503, detail="AI 服务未配置（OPENAI_API_KEY 未设置）")
        ep = _get_endpoint() or "https://api.openai.com/v1"
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{ep}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

@router.post("/nl2sql")
async def nl2sql(
    req: NL2SQLRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(DbConnection).where(DbConnection.id == req.connection_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")
    _check_conn_ownership(conn, current)

    cr = _get_conn_creds(conn)
    schema = await MySQLClient.get_schema(
        conn.id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])

    prompt = (
        f"Given this MySQL database schema:\n{schema}\n\n"
        f"Convert this natural language question to SQL:\n{req.question}\n"
        f"Return ONLY the SQL query, no explanation."
    )
    try:
        sql = await _call_llm(prompt, "You are a SQL expert. Return ONLY valid MySQL SQL.")
        return {
            "sql": sql.strip(),
            "explanation": f"Generated from schema of {cr['database']}",
            "confidence": 0.85,
            "schema_used": schema[:200] + "..."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 调用失败: {e}")

@router.post("/analyze-slow")
async def analyze_slow(
    req: AnalyzeSlowRequest,
    current: User = Depends(get_current_user)
):
    prompt = (
        "Analyze this MySQL query for performance issues.\n"
        "Return valid JSON with keys: type, suggestions (array), "
        "estimated_improvement, optimized_sql.\n\n"
        f"Query: {req.sql}"
    )
    try:
        result = await _call_llm(prompt,
            "You are a MySQL performance expert. Return valid JSON only.")
        return json.loads(result)
    except json.JSONDecodeError:
        return {
            "type": "analysis",
            "suggestions": [result],
            "estimated_improvement": "unknown",
            "optimized_sql": req.sql
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 调用失败: {e}")

@router.post("/chat")
async def ai_chat(
    req: ChatRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    system = (
        "You are RaoMySQL AI assistant. Help users with database queries, "
        "optimization, and management. Be concise and helpful."
    )
    if req.connection_id:
        result = await db.execute(
            select(DbConnection).where(DbConnection.id == req.connection_id))
        conn = result.scalar_one_or_none()
        if conn:
            _check_conn_ownership(conn, current)
            cr = _get_conn_creds(conn)
            schema = await MySQLClient.get_schema(
                conn.id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
            status = await MySQLClient.get_status(
                conn.id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
            system += (
                f"\n\nActive DB: {cr['database']}\n"
                f"Status: {json.dumps(status, default=str)}\n"
                f"Schema:\n{schema[:500]}"
            )
    try:
        resp = await _call_llm(req.message, system)
        return {"response": resp}
    except HTTPException:
        raise
    except Exception as e:
        return {"response": f"AI 不可用: {e}。请检查 /api/ai/config 配置。"}

@router.post("/review-sql")
async def review_sql(
    sql: str,
    current: User = Depends(get_current_user)
):
    su = sql.upper().strip()
    rules = []
    if "DROP" in su or "TRUNCATE" in su:
        rules.append("⚠️ 危险操作：DROP/TRUNCATE 已检测到")
    if "DELETE" in su and "WHERE" not in su:
        rules.append("⚠️ 危险操作：DELETE 缺少 WHERE 条件")
    if "UPDATE" in su and "WHERE" not in su:
        rules.append("⚠️ 危险操作：UPDATE 缺少 WHERE 条件")
    if "SELECT *" in su:
        rules.append("💡 建议：SELECT * 可能返回不必要的字段")
    if "LIKE '%" in su:
        rules.append("💡 建议：前导通配符无法使用索引")

    risk = "high" if any("⚠️" in r for r in rules) else ("medium" if rules else "low")

    if rules:
        prompt = f"Review this SQL:\n{sql}\nIssues: {rules}\nGive brief additional suggestions."
        try:
            advice = await _call_llm(prompt, "SQL 安全审查员。请简短回复。")
            rules.append(f"AI: {advice[:200]}")
        except Exception:
            pass
    return {"sql": sql, "risk": risk, "rules": rules}

@router.post("/analyze-alert")
async def analyze_alert(
    data: dict,
    current: User = Depends(get_current_user)
):
    prompt = f"分析以下数据库告警并给出操作建议：\n{json.dumps(data, ensure_ascii=False)}"
    try:
        resp = await _call_llm(prompt, "数据库运维专家。请给出可操作的步骤。")
        return {"analysis": resp}
    except Exception as e:
        return {"analysis": f"AI 不可用: {e}"}

@router.get("/config")
async def get_ai_config(current: User = Depends(get_current_user)):
    """返回 AI 配置（不暴露 API 密钥）"""
    key = _get_key()
    return {
        "provider": _get_provider(),
        "model": _get_model(),
        "endpoint": _get_endpoint(),
        "enabled": bool(key),
        # 不返回 key 本身，只告诉是否已配置
        "has_api_key": bool(key),
    }

@router.put("/config")
async def update_ai_config(
    cfg: AIConfigModel,
    current: User = Depends(get_current_user)
):
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可修改 AI 配置")
    if cfg.api_key:
        os.environ["OPENAI_API_KEY"] = cfg.api_key
        os.environ["AI_PROVIDER"] = cfg.provider
        os.environ["AI_MODEL"] = cfg.model
        if cfg.endpoint:
            os.environ["AI_ENDPOINT"] = cfg.endpoint
    return {"message": "配置已更新（仅内存生效，生产环境请修改 .env）"}
