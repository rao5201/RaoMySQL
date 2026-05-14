"""RaoMySQL Tasks Router v1.2 - Async DB + current_user.id Fix"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.database.init_db import get_db
from backend.database.models import ScheduledTask, TaskRun, User
from backend.routers.auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(prefix="/api/tasks", tags=["定时任务"])

class TaskCreate(BaseModel):
    name: str
    task_type: str
    cron_expr: Optional[str] = None
    config: Optional[str] = None

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    cron_expr: Optional[str] = None
    config: Optional[str] = None
    enabled: Optional[bool] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "developer"
    email: Optional[str] = None

class UserUpdate(BaseModel):
    role: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None

@router.get("")
async def get_tasks(
    task_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(ScheduledTask).where(ScheduledTask.user_id == current.id)
    if task_type:
        q = q.where(ScheduledTask.task_type == task_type)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    items = (await db.execute(
        q.order_by(ScheduledTask.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    )).scalars().all()
    return {"total": total, "page": page, "data": items}

@router.post("")
async def create_task(
    task_data: TaskCreate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = ScheduledTask(
        user_id=current.id, name=task_data.name, task_type=task_data.task_type,
        cron_expr=task_data.cron_expr, config=task_data.config, enabled=True
    )
    db.add(task); await db.commit(); await db.refresh(task)
    return task

@router.get("/{task_id}")
async def get_task(task_id: int, current: User = Depends(get_current_user),
                  db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).where(
        ScheduledTask.id == task_id, ScheduledTask.user_id == current.id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
    return task

@router.put("/{task_id}")
async def update_task(task_id: int, task_data: TaskUpdate,
                    current: User = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).where(
        ScheduledTask.id == task_id, ScheduledTask.user_id == current.id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
    for key, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    await db.commit(); await db.refresh(task)
    return task

@router.delete("/{task_id}")
async def delete_task(task_id: int, current: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).where(
        ScheduledTask.id == task_id, ScheduledTask.user_id == current.id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
    await db.delete(task); await db.commit()
    return {"message": "删除成功"}

@router.post("/{task_id}/run")
async def run_task_now(task_id: int, current: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).where(
        ScheduledTask.id == task_id, ScheduledTask.user_id == current.id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
    run = TaskRun(task_id=task_id, status="running", started_at=datetime.utcnow())
    db.add(run); await db.commit(); await db.refresh(run)
    # TODO: 根据 task.task_type 执行实际任务
    run.status = "success"; run.finished_at = datetime.utcnow()
    run.output = f"任务 {task.name} 执行完成"
    task.last_run_at = datetime.utcnow(); task.last_status = "success"
    await db.commit()
    return {"message": "任务已执行", "run_id": run.id}

@router.get("/{task_id}/runs")
async def get_task_runs(task_id: int, page: int = 1, page_size: int = 20,
                       current: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).where(
        ScheduledTask.id == task_id, ScheduledTask.user_id == current.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="任务不存在")
    runs_q = select(TaskRun).where(TaskRun.task_id == task_id
        ).order_by(TaskRun.started_at.desc()).offset((page-1)*page_size).limit(page_size)
    runs = (await db.execute(runs_q)).scalars().all()
    return {"task_id": task_id, "data": runs}

# ==================== 用户管理（管理员） ====================

@router.get("/users")
async def get_all_users(role: Optional[str] = None, page: int = 1, page_size: int = 20,
                       current: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    q = select(User)
    if role: q = q.where(User.role == role)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    users = (await db.execute(
        q.order_by(User.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    )).scalars().all()
    return {"total": total, "data": [{"id": u.id, "username": u.username,
        "role": u.role, "email": u.email, "status": u.status,
        "created_at": str(u.created_at)} for u in users]}

@router.post("/users")
async def create_user(user_data: UserCreate, current: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    existing = (await db.execute(
        select(User).where(User.username == user_data.username))).scalar_one_or_none()
    if existing: raise HTTPException(status_code=400, detail="用户名已存在")
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        username=user_data.username,
        password=pwd_ctx.hash(user_data.password),
        role=user_data.role, email=user_data.email
    )
    db.add(user); await db.commit(); await db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role,
            "email": user.email, "status": user.status}

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="用户不存在")
    await db.delete(user); await db.commit()
    return {"message": "删除成功"}

@router.put("/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate,
                    current: User = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="用户不存在")
    for key, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await db.commit()
    return {"id": user.id, "username": user.username, "role": user.role,
            "email": user.email, "status": user.status}
