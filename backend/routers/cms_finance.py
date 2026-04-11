"""
RaoCMS - 财务管理路由
销售分析、费用分析、财务报表
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from backend.database.cms_models import FinanceRecord, FinanceDailyStat, SalesRecord
from .cms_auth import get_current_user, require_finance, UserRole, Permission, require_permissions
from backend.database.init_db import get_db
from sqlalchemy import func, cast, Date

router = APIRouter(prefix="/api/finance", tags=["财务管理"])


# ==================== Pydantic 模型 ====================

class FinanceRecordCreate(BaseModel):
    record_type: str  # income/expense
    category: str
    amount: float
    title: str
    description: Optional[str] = None
    related_id: Optional[int] = None
    related_type: Optional[str] = None
    record_date: Optional[str] = None  # YYYY-MM-DD


class FinanceRecordUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[float] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class FinanceStatsResponse(BaseModel):
    total_income: float
    total_expense: float
    profit: float
    order_count: int
    avg_order_value: float


# ==================== 收支记录管理 ====================

@router.get("/records", response_model=List[dict])
async def get_finance_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    record_type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_permissions([Permission.FINANCE_VIEW])),
    db: Session = Depends(get_db)
):
    """获取收支记录列表"""
    query = db.query(FinanceRecord)
    
    if record_type:
        query = query.filter(FinanceRecord.record_type == record_type)
    if category:
        query = query.filter(FinanceRecord.category == category)
    if start_date:
        query = query.filter(FinanceRecord.record_date >= start_date)
    if end_date:
        query = query.filter(FinanceRecord.record_date <= end_date)
    
    total = query.count()
    records = query.order_by(FinanceRecord.record_date.desc(), FinanceRecord.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    result = []
    for r in records:
        result.append({
            "id": r.id,
            "record_type": r.record_type,
            "category": r.category,
            "amount": float(r.amount),
            "title": r.title,
            "description": r.description,
            "related_id": r.related_id,
            "related_type": r.related_type,
            "operator_id": r.operator_id,
            "record_date": r.record_date,
            "created_at": r.created_at
        })
    
    return result


@router.post("/records")
async def create_finance_record(
    record_data: FinanceRecordCreate,
    current_user: dict = Depends(require_permissions([Permission.FINANCE_MANAGE])),
    db: Session = Depends(get_db)
):
    """创建收支记录"""
    # 验证类别
    valid_categories = ["销售", "退款", "运营", "营销", "人力", "供应商", "物流", "其他"]
    if record_data.category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"无效的类别: {record_data.category}")
    
    record = FinanceRecord(
        record_type=record_data.record_type,
        category=record_data.category,
        amount=record_data.amount,
        title=record_data.title,
        description=record_data.description,
        related_id=record_data.related_id,
        related_type=record_data.related_type,
        operator_id=current_user.get("id"),
        record_date=record_data.record_date or datetime.utcnow().strftime("%Y-%m-%d")
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record


@router.get("/stats")
async def get_finance_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_permissions([Permission.FINANCE_VIEW])),
    db: Session = Depends(get_db)
):
    """获取财务统计概览"""
    # 默认查询最近30天
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 收入统计
    income = db.query(func.sum(FinanceRecord.amount)).filter(
        FinanceRecord.record_type == "income",
        FinanceRecord.record_date >= start_date,
        FinanceRecord.record_date <= end_date
    ).scalar() or 0
    
    # 支出统计
    expense = db.query(func.sum(FinanceRecord.amount)).filter(
        FinanceRecord.record_type == "expense",
        FinanceRecord.record_date >= start_date,
        FinanceRecord.record_date <= end_date
    ).scalar() or 0
    
    # 订单统计
    order_count = db.query(func.count(SalesRecord.id)).filter(
        SalesRecord.status.in_(["paid", "shipped", "completed"]),
        func.date(SalesRecord.created_at) >= start_date,
        func.date(SalesRecord.created_at) <= end_date
    ).scalar() or 0
    
    avg_order_value = float(income) / order_count if order_count > 0 else 0
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_income": float(income),
        "total_expense": float(expense),
        "profit": float(income) - float(expense),
        "order_count": order_count,
        "avg_order_value": round(avg_order_value, 2)
    }


@router.get("/sales")
async def get_sales_analysis(
    period: str = Query("day", regex="^(day|week|month|year)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_permissions([Permission.FINANCE_VIEW])),
    db: Session = Depends(func)
):
    """销售分析"""
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 按日期聚合销售数据
    query = db.query(
        func.date(SalesRecord.created_at).label("date"),
        func.count(SalesRecord.id).label("order_count"),
        func.sum(SalesRecord.total_amount).label("total_amount")
    ).filter(
        SalesRecord.status.in_(["paid", "shipped", "completed"]),
        func.date(SalesRecord.created_at) >= start_date,
        func.date(SalesRecord.created_at) <= end_date
    ).group_by(func.date(SalesRecord.created_at)).order_by("date")
    
    results = query.all()
    
    chart_data = []
    for r in results:
        chart_data.append({
            "date": str(r.date),
            "order_count": r.order_count,
            "total_amount": float(r.total_amount) if r.total_amount else 0
        })
    
    # 计算趋势
    total_amount = sum(item["total_amount"] for item in chart_data)
    avg_daily = total_amount / len(chart_data) if chart_data else 0
    
    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_amount": total_amount,
        "avg_daily": round(avg_daily, 2),
        "chart_data": chart_data
    }


@router.get("/expenses")
async def get_expense_analysis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_permissions([Permission.FINANCE_VIEW])),
    db: Session = Depends(get_db)
):
    """费用分析"""
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 按类别汇总费用
    query = db.query(
        FinanceRecord.category,
        func.sum(FinanceRecord.amount).label("total")
    ).filter(
        FinanceRecord.record_type == "expense",
        FinanceRecord.record_date >= start_date,
        FinanceRecord.record_date <= end_date
    ).group_by(FinanceRecord.category).order_by(func.sum(FinanceRecord.amount).desc())
    
    results = query.all()
    
    total_expense = sum(float(r.total) for r in results)
    
    breakdown = []
    for r in results:
        percentage = (float(r.total) / total_expense * 100) if total_expense > 0 else 0
        breakdown.append({
            "category": r.category,
            "amount": float(r.total),
            "percentage": round(percentage, 1)
        })
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_expense": total_expense,
        "breakdown": breakdown
    }


@router.get("/report")
async def get_finance_report(
    report_type: str = Query("monthly", regex="^(daily|weekly|monthly|yearly)$"),
    year: int = Query(default=None),
    month: int = Query(default=None),
    current_user: dict = Depends(require_permissions([Permission.FINANCE_VIEW])),
    db: Session = Depends(get_db)
):
    """财务报表"""
    now = datetime.utcnow()
    
    if report_type == "monthly":
        if not year:
            year = now.year
        if not month:
            month = now.month
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
    elif report_type == "yearly":
        if not year:
            year = now.year
        start_date = f"{year}-01-01"
        end_date = f"{year + 1}-01-01"
    else:
        start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")
    
    # 收入明细
    income_query = db.query(
        FinanceRecord.category,
        func.sum(FinanceRecord.amount).label("total")
    ).filter(
        FinanceRecord.record_type == "income",
        FinanceRecord.record_date >= start_date,
        FinanceRecord.record_date < end_date
    ).group_by(FinanceRecord.category)
    
    income_breakdown = [{"category": r.category, "amount": float(r.total)} for r in income_query.all()]
    total_income = sum(item["amount"] for item in income_breakdown)
    
    # 支出明细
    expense_query = db.query(
        FinanceRecord.category,
        func.sum(FinanceRecord.amount).label("total")
    ).filter(
        FinanceRecord.record_type == "expense",
        FinanceRecord.record_date >= start_date,
        FinanceRecord.record_date < end_date
    ).group_by(FinanceRecord.category)
    
    expense_breakdown = [{"category": r.category, "amount": float(r.total)} for r in expense_query.all()]
    total_expense = sum(item["amount"] for item in expense_breakdown)
    
    return {
        "report_type": report_type,
        "period": {"start": start_date, "end": end_date},
        "income": {
            "total": total_income,
            "breakdown": income_breakdown
        },
        "expense": {
            "total": total_expense,
            "breakdown": expense_breakdown
        },
        "profit": total_income - total_expense,
        "profit_margin": round((total_income - total_expense) / total_income * 100, 2) if total_income > 0 else 0
    }


@router.get("/trends")
async def get_finance_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: dict = Depends(require_permissions([Permission.FINANCE_VIEW])),
    db: Session = Depends(get_db)
):
    """财务趋势（收入/支出/利润曲线）"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 按日统计
    query = db.query(
        FinanceRecord.record_date,
        FinanceRecord.record_type,
        func.sum(FinanceRecord.amount).label("total")
    ).filter(
        FinanceRecord.record_date >= start_date.strftime("%Y-%m-%d"),
        FinanceRecord.record_date <= end_date.strftime("%Y-%m-%d")
    ).group_by(FinanceRecord.record_date, FinanceRecord.record_type).order_by(FinanceRecord.record_date)
    
    results = query.all()
    
    # 转换为字典
    daily_data = {}
    for r in results:
        date = r.record_date
        if date not in daily_data:
            daily_data[date] = {"income": 0, "expense": 0}
        daily_data[date][r.record_type] = float(r.total)
    
    # 转换为列表
    chart_data = []
    for date, data in sorted(daily_data.items()):
        chart_data.append({
            "date": date,
            "income": data["income"],
            "expense": data["expense"],
            "profit": data["income"] - data["expense"]
        })
    
    return {
        "days": days,
        "chart_data": chart_data
    }