"""
RaoCMS - 权限控制模块
基于角色的权限控制（RBAC）
"""

from enum import Enum
from functools import wraps
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 配置
SECRET_KEY = "raocms-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# 安全方案
security = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"              # 管理员 - 全部权限
    CUSTOMER_SERVICE = "customer_service"  # 客服 - 查看/添加文章，上传文件
    FINANCE = "finance"          # 财务 - 查看财务数据


class Permission(str, Enum):
    """权限枚举"""
    # 文章权限
    ARTICLE_VIEW = "article:view"
    ARTICLE_CREATE = "article:create"
    ARTICLE_EDIT = "article:edit"
    ARTICLE_DELETE = "article:delete"
    ARTICLE_AUDIT = "article:audit"  # 审核权限
    
    # 文件权限
    FILE_VIEW = "file:view"
    FILE_UPLOAD = "file:upload"
    FILE_DELETE = "file:delete"
    
    # 用户权限
    USER_VIEW = "user:view"
    USER_MANAGE = "user:manage"  # 创建/编辑/删除用户
    
    # 前台用户权限
    PORTAL_USER_VIEW = "portal_user:view"
    PORTAL_USER_MANAGE = "portal_user:manage"
    
    # 供应商权限
    SUPPLIER_VIEW = "supplier:view"
    SUPPLIER_MANAGE = "supplier:manage"
    
    # 产品权限
    PRODUCT_VIEW = "product:view"
    PRODUCT_MANAGE = "product:manage"
    
    # 财务权限
    FINANCE_VIEW = "finance:view"
    FINANCE_MANAGE = "finance:manage"
    
    # 系统权限
    SYSTEM_SETTING = "system:setting"
    SYSTEM_LOG = "system:log"


# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # 管理员拥有所有权限
        Permission.ARTICLE_VIEW, Permission.ARTICLE_CREATE, Permission.ARTICLE_EDIT, 
        Permission.ARTICLE_DELETE, Permission.ARTICLE_AUDIT,
        Permission.FILE_VIEW, Permission.FILE_UPLOAD, Permission.FILE_DELETE,
        Permission.USER_VIEW, Permission.USER_MANAGE,
        Permission.PORTAL_USER_VIEW, Permission.PORTAL_USER_MANAGE,
        Permission.SUPPLIER_VIEW, Permission.SUPPLIER_MANAGE,
        Permission.PRODUCT_VIEW, Permission.PRODUCT_MANAGE,
        Permission.FINANCE_VIEW, Permission.FINANCE_MANAGE,
        Permission.SYSTEM_SETTING, Permission.SYSTEM_LOG,
    ],
    UserRole.CUSTOMER_SERVICE: [
        # 客服权限：查看文章、添加文章（需审核）、查看文件、上传文件
        Permission.ARTICLE_VIEW, Permission.ARTICLE_CREATE,
        Permission.FILE_VIEW, Permission.FILE_UPLOAD,
    ],
    UserRole.FINANCE: [
        # 财务权限：查看供应商、产品、财务数据
        Permission.SUPPLIER_VIEW,
        Permission.PRODUCT_VIEW,
        Permission.FINANCE_VIEW, Permission.FINANCE_MANAGE,
    ],
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """获取当前登录用户"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证凭证")
    
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证凭证")
    
    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")
    
    if not user_id or not username or not role:
        raise HTTPException(status_code=401, detail="无效的认证信息")
    
    return {
        "id": int(user_id),
        "username": username,
        "role": role,
    }


def require_permissions(required_permissions: List[Permission]):
    """权限检查装饰器"""
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if not user_role:
            raise HTTPException(status_code=403, detail="无法获取用户角色")
        
        # 获取用户角色的所有权限
        user_permissions = ROLE_PERMISSIONS.get(UserRole(user_role), [])
        
        # 检查是否拥有所需权限
        for perm in required_permissions:
            if perm not in user_permissions:
                raise HTTPException(
                    status_code=403, 
                    detail=f"权限不足，缺少权限: {perm.value}"
                )
        
        return current_user
    return permission_checker


def require_role(required_roles: List[UserRole]):
    """角色检查装饰器"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if not user_role:
            raise HTTPException(status_code=403, detail="无法获取用户角色")
        
        if UserRole(user_role) not in required_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"权限不足，需要角色: {[r.value for r in required_roles]}"
            )
        
        return current_user
    return role_checker


# 常用权限组合（便于使用）
require_admin = require_role([UserRole.ADMIN])
require_staff = require_role([UserRole.ADMIN, UserRole.CUSTOMER_SERVICE])
require_finance = require_role([UserRole.ADMIN, UserRole.FINANCE])

# 特定权限检查
require_article_manage = require_permissions([
    Permission.ARTICLE_VIEW, Permission.ARTICLE_CREATE, 
    Permission.ARTICLE_EDIT, Permission.ARTICLE_DELETE
])
require_article_audit = require_permissions([Permission.ARTICLE_AUDIT])
require_user_manage = require_permissions([Permission.USER_MANAGE])
require_finance_manage = require_permissions([Permission.FINANCE_MANAGE])
