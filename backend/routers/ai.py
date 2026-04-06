"""
RaoMySQL - AI 助手路由
自然语言转 SQL、慢查询分析、智能告警
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from backend.database.init_db import get_db
from backend.routers.auth import get_current_user
import os

router = APIRouter(prefix="/api/ai", tags=["AI助手"])


class NL2SQLRequest(BaseModel):
    question: str
    connection_id: Optional[int] = None


class NL2SQLResponse(BaseModel):
    sql: str
    explanation: str
    confidence: float


class AnalyzeSlowQueryRequest(BaseModel):
    sql: str
    connection_id: Optional[int] = None


class AIChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class AIChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None


# ==================== 自然语言转 SQL ====================

@router.post("/nl2sql", response_model=NL2SQLResponse)
async def natural_language_to_sql(
    request: NL2SQLRequest,
    current_user: dict = Depends(get_current_user)
):
    """自然语言转 SQL"""
    # TODO: 接入 LangChain + OpenAI 实现
    # 1. 获取数据库表结构
    # 2. 使用 LLM 生成 SQL
    # 3. 返回 SQL 和解释
    
    # 模拟返回
    return NL2SQLResponse(
        sql="SELECT * FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
        explanation="查询过去7天内注册的用户",
        confidence=0.85
    )


# ==================== 慢查询分析 ====================

@router.post("/analyze-slow")
async def analyze_slow_query(
    request: AnalyzeSlowQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """分析慢查询并给出优化建议"""
    # TODO: 接入 LangChain 分析慢查询
    
    return {
        "sql": request.sql,
        "analysis": {
            "type": "全表扫描",
            "suggestions": [
                "建议在 status 字段上添加索引",
                "考虑使用覆盖索引避免回表",
                "可以将 LIMIT 分页改为游标分页"
            ],
            "estimated_improvement": "70%"
        },
        "optimized_sql": "SELECT * FROM orders FORCE INDEX(idx_status) WHERE status = 'completed'"
    }


# ==================== AI 对话 ====================

@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    request: AIChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """AI 对话（智能助手）"""
    # TODO: 接入 LangChain 实现对话
    
    message = request.message.lower()
    
    if "查询" in message or "select" in message:
        response = "我可以帮你将自然语言转换为 SQL。请描述你想要查询的数据，例如：'查询过去一周的订单数量'"
    elif "优化" in message or "slow" in message:
        response = "我可以帮你分析慢查询并提供优化建议。请提供需要分析的 SQL 语句。"
    elif "备份" in message:
        response = "我可以帮你创建数据库备份。请在备份页面选择要备份的数据库连接。"
    elif "监控" in message:
        response = "我可以帮你分析数据库监控数据。你想查看哪个连接的状态？"
    else:
        response = "你好！我是 RaoMySQL AI 助手，可以帮你：\n1. 自然语言转 SQL\n2. 慢查询分析\n3. 数据库状态查询\n4. 操作建议"
    
    return AIChatResponse(
        response=response,
        suggestions=[
            "帮我查询过去7天的销售数据",
            "分析这个慢查询",
            "查看数据库健康状态"
        ]
    )


# ==================== AI 配置 ====================

class AIConfig(BaseModel):
    provider: str  # openai/ollama
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    model: str = "gpt-4"


@router.get("/config")
async def get_ai_config(
    current_user: dict = Depends(get_current_user)
):
    """获取 AI 配置"""
    # 从环境变量或配置文件读取
    return {
        "provider": os.getenv("AI_PROVIDER", "openai"),
        "model": os.getenv("AI_MODEL", "gpt-4"),
        "endpoint": os.getenv("AI_ENDPOINT", ""),
        "enabled": bool(os.getenv("OPENAI_API_KEY", ""))
    }


@router.put("/config")
async def update_ai_config(
    config: AIConfig,
    current_user: dict = Depends(get_current_user)
):
    """更新 AI 配置（仅管理员）"""
    if current_user.get("role") != "admin":
        return {"error": "仅管理员可配置"}
    
    # TODO: 保存配置到文件或数据库
    return {"message": "配置已更新", "config": config.dict()}


# ==================== 智能告警 ====================

@router.post("/analyze-alert")
async def analyze_alert(
    alert_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """AI 分析告警并给出建议"""
    # TODO: 使用 AI 分析告警原因和解决方案
    
    level = alert_data.get("level", "info")
    title = alert_data.get("title", "")
    
    analysis = {
        "critical": {
            "reason": "数据库连接数接近上限，可能导致服务不可用",
            "actions": [
                "立即检查连接泄漏",
                "增加 max_connections 配置",
                "重启占用连接的应用"
            ]
        },
        "warning": {
            "reason": "磁盘空间使用率较高",
            "actions": [
                "清理不必要的日志文件",
                "删除过期备份",
                "考虑扩容"
            ]
        },
        "info": {
            "reason": "常规监控信息",
            "actions": ["无需处理"]
        }
    }
    
    return analysis.get(level, analysis["info"])


# ==================== SQL 审查 ====================

@router.post("/review-sql")
async def review_sql(
    sql: str,
    current_user: dict = Depends(get_current_user)
):
    """SQL 语句审查（执行前风险评估）"""
    # TODO: 使用 AI 分析 SQL 风险
    
    sql_upper = sql.upper().strip()
    
    # 简单规则判断
    if "DROP" in sql_upper or "TRUNCATE" in sql_upper:
        risk = "high"
        message = "检测到危险操作，建议仔细确认"
    elif "DELETE" in sql_upper and "WHERE" not in sql_upper:
        risk = "high"
        message = "检测到无 WHERE 条件的 DELETE，可能导致数据清空"
    elif "UPDATE" in sql_upper and "WHERE" not in sql_upper:
        risk = "high"
        message = "检测到无 WHERE 条件的 UPDATE，可能导致全表更新"
    else:
        risk = "low"
        message = "SQL 语句看起来正常"
    
    return {
        "sql": sql,
        "risk": risk,
        "message": message,
        "suggestions": [
            "建议先在测试环境执行",
            "确保有数据备份"
        ]
    }