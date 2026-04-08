"""RaoMySQL AI Router v1.1 - Real LLM support (OpenAI/Ollama)"""
import os, json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from backend.database.init_db import get_db
from backend.database.models import DbConnection
from backend.routers.auth import get_current_user
from backend.utils.crypto import decrypt_password
from backend.services.mysql_client import MySQLClient

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

def _get_provider():
    return os.getenv("AI_PROVIDER", "openai")

def _get_model():
    return os.getenv("AI_MODEL", "gpt-4")

def _get_endpoint():
    return os.getenv("AI_ENDPOINT", "")

def _get_key():
    return os.getenv("OPENAI_API_KEY", "")

def _get_conn_creds(conn, db):
    pw = decrypt_password(conn.password_enc) if conn.password_enc else ""
    return {"host": conn.host, "port": conn.port, "user": conn.username,
            "pw": pw, "database": conn.database}

async def _call_llm(prompt, system="You are a helpful database assistant."):
    import httpx
    provider = _get_provider()
    model = _get_model()
    if provider == "ollama":
        ep = _get_endpoint() or "http://localhost:11434"
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{ep}/api/chat", json={"model": model,
                "messages": [{"role":"system","content":system},{"role":"user","content":prompt}]})
            r.raise_for_status()
            return r.json()["message"]["content"]
    else:
        key = _get_key()
        if not key: raise HTTPException(503, "OPENAI_API_KEY not set")
        ep = _get_endpoint() or "https://api.openai.com/v1"
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{ep}/chat/completions",
                headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                json={"model": model, "messages": [
                    {"role":"system","content":system},{"role":"user","content":prompt}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

@router.post("/nl2sql")
async def nl2sql(req: NL2SQLRequest, current_user=Depends(get_current_user),
                 db=Depends(get_db)):
    conn = db.query(DbConnection).filter(
        DbConnection.id==req.connection_id,
        DbConnection.user_id==current_user.get("id")).first()
    if not conn: raise HTTPException(404,"connection not found")
    cr = _get_conn_creds(conn, db)
    schema = await MySQLClient.get_schema(
        req.connection_id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
    prompt = f"Given this database schema:\n{schema}\n\nConvert to SQL: {req.question}\nReturn ONLY the SQL, no explanation."
    try:
        sql = await _call_llm(prompt, "You are a SQL expert. Return ONLY valid MySQL SQL.")
        return {"sql": sql.strip(), "explanation": f"Generated from schema of {cr['database']}",
                "confidence": 0.85, "schema_used": schema[:200]+"..."}
    except Exception as e:
        raise HTTPException(500, f"LLM error: {e}")

@router.post("/analyze-slow")
async def analyze_slow(req: AnalyzeSlowRequest, current_user=Depends(get_current_user)):
    prompt = f"""Analyze this MySQL query for performance issues and suggest optimizations.
Return JSON with keys: type, suggestions (array), estimated_improvement, optimized_sql.

Query: {req.sql}"""
    try:
        result = await _call_llm(prompt, "You are a MySQL performance expert. Return valid JSON only.")
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"type": "analysis", "suggestions": [result],
                    "estimated_improvement": "unknown", "optimized_sql": req.sql}
    except Exception as e:
        raise HTTPException(500, f"LLM error: {e}")

@router.post("/chat")
async def ai_chat(req: ChatRequest, current_user=Depends(get_current_user),
                  db=Depends(get_db)):
    system = "You are RaoMySQL AI assistant. Help users with database queries, optimization, and management. Be concise."
    if req.connection_id:
        conn = db.query(DbConnection).filter(
            DbConnection.id==req.connection_id,
            DbConnection.user_id==current_user.get("id")).first()
        if conn:
            cr = _get_conn_creds(conn, db)
            schema = await MySQLClient.get_schema(
                req.connection_id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
            status = await MySQLClient.get_status(
                req.connection_id, cr["host"], cr["port"], cr["user"], cr["pw"], cr["database"])
            system += f"\nActive DB: {cr['database']}\nStatus: {json.dumps(status, default=str)}\nSchema:\n{schema[:500]}"
    try:
        resp = await _call_llm(req.message, system)
        return {"response": resp}
    except Exception as e:
        return {"response": f"AI unavailable: {e}. Please check AI config in /api/ai/config"}

@router.post("/review-sql")
async def review_sql(sql: str, current_user=Depends(get_current_user)):
    su = sql.upper().strip()
    rules = []
    if "DROP" in su or "TRUNCATE" in su: rules.append("DANGER: DROP/TRUNCATE detected")
    if "DELETE" in su and "WHERE" not in su: rules.append("DANGER: DELETE without WHERE")
    if "UPDATE" in su and "WHERE" not in su: rules.append("DANGER: UPDATE without WHERE")
    if "SELECT *" in su: rules.append("WARN: SELECT * may return unnecessary columns")
    if "LIKE '%" in su: rules.append("WARN: Leading wildcard prevents index use")
    risk = "high" if any("DANGER" in r for r in rules) else ("medium" if rules else "low")
    if rules:
        prompt = f"Review this SQL for risks:\n{sql}\nRules found: {rules}\nGive brief additional suggestions."
        try:
            ai_advice = await _call_llm(prompt, "SQL security reviewer. Be brief.")
            rules.append(f"AI: {ai_advice[:200]}")
        except: pass
    return {"sql": sql, "risk": risk, "rules": rules}

@router.post("/analyze-alert")
async def analyze_alert(data: dict, current_user=Depends(get_current_user)):
    prompt = f"Analyze this database alert and suggest actions: {json.dumps(data)}"
    try:
        resp = await _call_llm(prompt, "Database operations expert. Give actionable steps.")
        return {"analysis": resp}
    except Exception as e:
        return {"analysis": f"AI unavailable: {e}"}

@router.get("/config")
async def get_ai_config(current_user=Depends(get_current_user)):
    return {"provider": _get_provider(), "model": _get_model(),
            "endpoint": _get_endpoint(), "enabled": bool(_get_key())}

@router.put("/config")
async def update_ai_config(cfg: AIConfigModel, current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "admin only")
    if cfg.api_key:
        os.environ["OPENAI_API_KEY"] = cfg.api_key
        os.environ["AI_PROVIDER"] = cfg.provider
        os.environ["AI_MODEL"] = cfg.model
        if cfg.endpoint: os.environ["AI_ENDPOINT"] = cfg.endpoint
    return {"message": "config updated (runtime only, set env vars for persistence)"}
