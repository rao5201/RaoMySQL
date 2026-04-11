"""认证路由：注册/登录/JWT"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from backend.database.init_db import get_db
from backend.database.models import User
from .auth_schemas import UserCreate, UserLogin, UserOut, Token, TokenData
from backend.config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])

# 主哈希方案（bcrypt，用于新密码）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 备用方案：sha256_crypt（bcrypt 不可用时降级使用）
_fallback_ctx = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain: str, hashed: str) -> bool:
    """验证密码，尝试多种哈希方案"""
    # 优先 bcrypt（标准方案）
    try:
        if pwd_context.verify(plain, hashed):
            return True
    except Exception:
        pass
    # 降级尝试 sha256_crypt（兼容旧版或 bcrypt 异常时）
    try:
        if _fallback_ctx.verify(plain, hashed):
            return True
    except Exception:
        pass
    return False

def hash_password(password: str) -> str:
    """生成密码哈希，优先 bcrypt，bcrypt 不可用时降级 sha256_crypt"""
    try:
        return pwd_context.hash(password)
    except Exception:
        # bcrypt 失败时降级到 sha256_crypt（功能降级但系统可用）
        return _fallback_ctx.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token 已失效或无效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    if user.status == "disabled":
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user

async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user

@router.post("/register", response_model=UserOut)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=user_data.username,
        password=hash_password(user_data.password),
        email=user_data.email,
        role=user_data.role or "viewer",
        status="active"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut(
        id=user.id,
        username=user.username,
        role=user.role,
        email=user.email,
        status=user.status,
        created_at=str(user.created_at)
    )

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status == "disabled":
        raise HTTPException(status_code=403, detail="账号已被禁用")
    access_token = create_access_token(data={"user_id": user.id, "username": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def get_me(current: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserOut(
        id=current.id,
        username=current.username,
        role=current.role,
        email=current.email,
        status=current.status,
        created_at=str(current.created_at)
    )
