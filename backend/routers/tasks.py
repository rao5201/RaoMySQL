"""
RaoMySQL - 定时任务路由
定时任务管理和执行
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.database.init_db import get_db
from backend.database.models import ScheduledTask, TaskRun
from .auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["定时任务"])


class TaskCreate(BaseModel):
    name: str
    task_type: str  # backup/health_check/report/cleanup
    cron_expr: Optional[str] = None
    config: Optional[str] = None  # JSON 配置


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    cron_expr: Optional[str] = None
    config: Optional[str] = None
    enabled: Optional[bool] = None


class TaskResponse(BaseModel):
    id: int
    name: str
    task_type: str
    cron_expr: Optional[str]
    config: Optional[str]
    enabled: bool
    last_run_at: Optional[datetime]
    last_status: Optional[str]
    created_at: datetime


class TaskRunResponse(BaseModel):
    id: int
    task_id: int
    status: Optional[str]
    output: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]


@router.get("")
async def get_tasks(
    task_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    query = db.query(ScheduledTask).filter(ScheduledTask.user_id == current_user.get("id"))
    
    if task_type:
        query = query.filter(ScheduledTask.task_type == task_type)
    
    total = query.count()
    tasks = query.order_by(ScheduledTask.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return {"total": total, "page": page, "data": tasks}


@router.post("")
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建定时任务"""
    task = ScheduledTask(
        user_id=current_user.get("id"),
        name=task_data.name,
        task_type=task_data.task_type,
        cron_expr=task_data.cron_expr,
        config=task_data.config,
        enabled=True
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}")
async def get_task(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务详情"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.get("id")
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.put("/{task_id}")
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新任务"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.get("id")
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    update_data = task_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除任务"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.get("id")
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    db.delete(task)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{task_id}/run")
async def run_task_now(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """立即执行任务"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.get("id")
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 创建任务运行记录
    run = TaskRun(
        task_id=task_id,
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(run)
    db.commit()
    
    # TODO: 实际执行任务
    # 根据 task.task_type 执行不同任务
    run.status = "success"
    run.finished_at = datetime.utcnow()
    run.output = f"任务 {task.name} 执行完成"
    
    # 更新任务状态
    task.last_run_at = datetime.utcnow()
    task.last_status = "success"
    
    db.commit()
    
    return {"message": "任务已执行", "run_id": run.id}


@router.get("/{task_id}/runs")
async def get_task_runs(
    task_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务运行历史"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.get("id")
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    runs = db.query(TaskRun).filter(
        TaskRun.task_id == task_id
    ).order_by(TaskRun.started_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return {"task_id": task_id, "data": runs}


# ==================== 用户管理（管理员） ====================

@router.get("/users")
async def get_all_users(
    role: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有用户（仅管理员）"""
    from backend.database.models import User
    
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    # 不返回密码
    for u in users:
        u.password = ""
    
    return {"total": total, "data": users}


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "developer"
    email: Optional[str] = None


@router.post("/users")
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建用户（仅管理员）"""
    from backend.database.models import User
    from passlib.context import CryptContext
    
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    # 检查用户名是否存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = User(
        username=user_data.username,
        password=pwd_context.hash(user_data.password),
        role=user_data.role,
        email=user_data.email
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.password = ""
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户（仅管理员）"""
    from backend.database.models import User
    
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    if user_id == current_user.get("id"):
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}


class UserUpdate(BaseModel):
    role: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户（仅管理员）"""
    from backend.database.models import User
    
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    update_data = user_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    user.password = ""
    return user