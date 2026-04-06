"""
RaoCMS - 文章管理路由
包含文章 CRUD、审核流程
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.database.cms_models import Article, Category, ArticleAudit, SysUser
from backend.routers.cms_auth import get_current_user, require_staff, UserRole, Permission, require_permissions
from backend.database.init_db import get_db
import json

router = APIRouter(prefix="/api/articles", tags=["文章管理"])


# ==================== Pydantic 模型 ====================

class ArticleCreate(BaseModel):
    title: str
    category_id: Optional[int] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    seo_title: Optional[str] = None
    seo_keywords: Optional[str] = None
    seo_description: Optional[str] = None
    is_top: bool = False


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[int] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    seo_title: Optional[str] = None
    seo_keywords: Optional[str] = None
    seo_description: Optional[str] = None
    is_top: Optional[bool] = None


class ArticleAuditRequest(BaseModel):
    comment: Optional[str] = None


class ArticleResponse(BaseModel):
    id: int
    title: str
    category_id: Optional[int]
    summary: Optional[str]
    content: Optional[str]
    cover_image: Optional[str]
    author_id: Optional[int]
    author_name: Optional[str]
    status: str
    is_top: bool
    view_count: int
    published_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 路由实现 ====================

@router.get("", response_model=List[ArticleResponse])
async def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文章列表"""
    query = db.query(Article)
    
    # 权限过滤
    user_role = current_user.get("role")
    if user_role != UserRole.ADMIN.value:
        # 非管理员只能看到自己创建的和已发布的
        query = query.filter(Article.author_id == current_user.get("id"))
    
    # 筛选条件
    if category_id:
        query = query.filter(Article.category_id == category_id)
    if status:
        query = query.filter(Article.status == status)
    if keyword:
        query = query.filter(Article.title.contains(keyword))
    
    # 分页
    total = query.count()
    articles = query.order_by(Article.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return articles


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文章详情"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    # 增加浏览量
    article.view_count += 1
    db.commit()
    
    return article


@router.post("", response_model=ArticleResponse)
async def create_article(
    article_data: ArticleCreate,
    current_user: dict = Depends(require_permissions([Permission.ARTICLE_CREATE])),
    db: Session = Depends(get_db)
):
    """创建文章（客服及以上权限）"""
    article = Article(
        title=article_data.title,
        category_id=article_data.category_id,
        summary=article_data.summary,
        content=article_data.content,
        cover_image=article_data.cover_image,
        author_id=current_user.get("id"),
        author_name=current_user.get("username"),
        status="draft",  # 草稿状态
        is_top=article_data.is_top,
        seo_title=article_data.seo_title,
        seo_keywords=article_data.seo_keywords,
        seo_description=article_data.seo_description,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    
    # 记录操作日志
    _log_operation(db, current_user.get("id"), "create", "article", f"创建文章: {article.title}")
    
    return article


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新文章"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    # 权限检查：只有管理员可以编辑任何文章，非管理员只能编辑自己的
    user_role = current_user.get("role")
    if user_role != UserRole.ADMIN.value and article.author_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="无权限编辑此文章")
    
    # 更新字段
    update_data = article_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(article, key, value)
    
    article.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(article)
    
    _log_operation(db, current_user.get("id"), "update", "article", f"更新文章: {article.title}")
    
    return article


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    current_user: dict = Depends(require_permissions([Permission.ARTICLE_DELETE])),
    db: Session = Depends(get_db)
):
    """删除文章（仅管理员）"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    title = article.title
    db.delete(article)
    db.commit()
    
    _log_operation(db, current_user.get("id"), "delete", "article", f"删除文章: {title}")
    
    return {"message": "删除成功"}


@router.post("/{article_id}/submit")
async def submit_article(
    article_id: int,
    current_user: dict = Depends(require_permissions([Permission.ARTICLE_CREATE])),
    db: Session = Depends(get_db)
):
    """提交审核"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    # 检查权限
    user_role = current_user.get("role")
    if user_role != UserRole.ADMIN.value and article.author_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="无权限操作此文章")
    
    article.status = "pending"  # 待审核状态
    db.commit()
    
    # 记录审核日志
    audit = ArticleAudit(
        article_id=article.id,
        operator_id=current_user.get("id"),
        action="submit",
        comment="提交审核"
    )
    db.add(audit)
    db.commit()
    
    _log_operation(db, current_user.get("id"), "submit", "article", f"提交审核: {article.title}")
    
    return {"message": "提交审核成功"}


@router.post("/{article_id}/approve")
async def approve_article(
    article_id: int,
    audit_data: ArticleAuditRequest = None,
    current_user: dict = Depends(require_permissions([Permission.ARTICLE_AUDIT])),
    db: Session = Depends(get_db)
):
    """审核通过"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    article.status = "published"  # 已发布
    article.published_at = datetime.utcnow()
    db.commit()
    
    # 记录审核日志
    audit = ArticleAudit(
        article_id=article.id,
        operator_id=current_user.get("id"),
        action="approve",
        comment=audit_data.comment if audit_data else None
    )
    db.add(audit)
    db.commit()
    
    _log_operation(db, current_user.get("id"), "approve", "article", f"审核通过: {article.title}")
    
    return {"message": "审核通过"}


@router.post("/{article_id}/reject")
async def reject_article(
    article_id: int,
    audit_data: ArticleAuditRequest,
    current_user: dict = Depends(require_permissions([Permission.ARTICLE_AUDIT])),
    db: Session = Depends(get_db)
):
    """审核驳回"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    article.status = "rejected"  # 已驳回
    db.commit()
    
    # 记录审核日志
    audit = ArticleAudit(
        article_id=article.id,
        operator_id=current_user.get("id"),
        action="reject",
        comment=audit_data.comment if audit_data else "审核驳回"
    )
    db.add(audit)
    db.commit()
    
    _log_operation(db, current_user.get("id"), "reject", "article", f"审核驳回: {article.title}")
    
    return {"message": "审核驳回"}


@router.post("/{article_id}/offline")
async def offline_article(
    article_id: int,
    audit_data: ArticleAuditRequest = None,
    current_user: dict = Depends(require_permissions([Permission.ARTICLE_DELETE])),
    db: Session = Depends(get_db)
):
    """下架文章"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    article.status = "offline"
    db.commit()
    
    # 记录审核日志
    audit = ArticleAudit(
        article_id=article.id,
        operator_id=current_user.get("id"),
        action="offline",
        comment=audit_data.comment if audit_data else "文章下架"
    )
    db.add(audit)
    db.commit()
    
    _log_operation(db, current_user.get("id"), "offline", "article", f"下架文章: {article.title}")
    
    return {"message": "下架成功"}


# ==================== 辅助函数 ====================

def _log_operation(db, user_id: int, action: str, module: str, detail: str):
    """记录操作日志"""
    from backend.database.cms_models import OperationLog
    log = OperationLog(
        user_id=user_id,
        user_type="sys",
        action=action,
        module=module,
        detail=detail
    )
    db.add(log)
    db.commit()
