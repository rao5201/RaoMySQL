"""
Unified Authentication Service
Single JWT token works across all Rao* systems.
Token contains: user_id, role, permissions, systems (which systems they can access)
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .unified_models import User, UserRole, UserSession
from .init_db import get_db

# Config
SECRET_KEY = os.getenv("UNIFIED_SECRET_KEY", "rao-unified-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "24"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_unified_token(
    user: User,
    system: str = "raomysql",  # Which system issued the token
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT token that works across all systems"""
    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    expire = datetime.utcnow() + expires_delta
    
    # Parse permissions
    perms = json.loads(user.permissions or "{}")
    
    # Determine accessible systems
    accessible_systems = []
    for sys in ["raomysql", "raocms", "raofm"]:
        if user.can_access_system(sys):
            accessible_systems.append(sys)
    
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "permissions": perms,
        "systems": accessible_systems,
        "system": system,  # Issuing system
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token"""
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user

def get_current_user_for_system(
    system: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get user and verify they can access specific system"""
    token = credentials.credentials
    payload = decode_token(token)
    
    # Check system access
    accessible_systems = payload.get("systems", [])
    if system not in accessible_systems:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to {system}. Your role: {payload.get('role')}"
        )
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user

def require_role(allowed_roles: list):
    """Decorator to require specific role"""
    def decorator(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role {user.role} not authorized. Required: {allowed_roles}"
            )
        return user
    return decorator

def require_permission(system: str, action: str):
    """Decorator to require specific permission"""
    def decorator(user: User = Depends(get_current_user)):
        if not user.has_permission(system, action):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {system}.{action}"
            )
        return user
    return decorator

# Role-based access helpers
class RoleChecker:
    """Helper class for role-based access control"""
    
    ADMIN_ONLY = ["admin"]
    FINANCE_ACCESS = ["admin", "finance"]
    SUPPORT_ACCESS = ["admin", "support"]
    SUPPLIER_ACCESS = ["admin", "supplier"]
    MERCHANT_ACCESS = ["admin", "merchant"]
    ALL_AUTHENTICATED = ["admin", "finance", "support", "supplier", "merchant", "user", "guest"]

# Permission templates for different roles
ROLE_PERMISSION_TEMPLATES = {
    "admin": {
        "raomysql": ["read", "write", "delete", "admin"],
        "raocms": ["read", "write", "delete", "admin", "publish", "finance"],
        "raofm": ["read", "write", "delete", "admin", "share"]
    },
    "finance": {
        "raocms": ["read", "finance"]  # Finance reports only
    },
    "support": {
        "raocms": ["read", "write"],  # Can add articles (needs review)
        "raofm": ["read", "write"]    # File management
    },
    "supplier": {
        "raocms": ["read", "write"]  # Own products only
    },
    "merchant": {
        "raocms": ["read", "write"]  # Own products/orders only
    },
    "user": {
        "raofm": ["read", "write"]  # Own files only
    },
    "guest": {
        "raocms": ["read"]  # Public content only
    }
}

def get_default_permissions(role: str) -> str:
    """Get default permissions for a role"""
    perms = ROLE_PERMISSION_TEMPLATES.get(role, {})
    return json.dumps(perms)