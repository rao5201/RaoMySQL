"""认证路由：注册/登录/JWT/邀请码"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets

from passlib.context import CryptContext
from backend.database.init_db import get_db
from backend.database.models import User, Invitation
from .auth_schemas import (
    UserCreate, UserLogin, UserOut, Token, TokenData,
    InviteCodeCreate, InviteCodeOut, InviteCodeList, RegisterWithInvite
)
from backend.config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])

# ── 密码哈希 ──
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_fallback_ctx = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        if pwd_context.verify(plain, hashed):
            return True
    except Exception:
        pass
    try:
        if _fallback_ctx.verify(plain, hashed):
            return True
    except Exception:
        pass
    return False

def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        return _fallback_ctx.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

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

# ── 公开信息 ──
@router.get("/public/config")
async def get_public_config():
    """返回公开的注册配置（前端据此决定显示哪种注册方式）"""
    return {
        "allow_registration": settings.ALLOW_REGISTRATION,
        "invite_required": settings.INVITE_REQUIRED,
        "app_name": settings.APP_NAME,
    }

# ── 普通注册（当 INVITE_REQUIRED=False 时可用） ──
@router.post("/register", response_model=UserOut)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前系统已关闭公开注册，请联系管理员获取邀请码"
        )
    if settings.INVITE_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前系统需要邀请码才能注册，请使用邀请链接"
        )

    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=user_data.username,
        password=hash_password(user_data.password),
        email=user_data.email,
        role=user_data.role or "developer",
        status="active"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut(
        id=user.id, username=user.username, role=user.role,
        email=user.email, status=user.status, created_at=str(user.created_at)
    )

# ── 邀请码注册 ──
@router.post("/register-with-invite", response_model=UserOut)
async def register_with_invite(
    data: RegisterWithInvite,
    db: AsyncSession = Depends(get_db)
):
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前系统已关闭注册"
        )

    # 校验邀请码
    result = await db.execute(
        select(Invitation).where(Invitation.code == data.invite_code)
    )
    invite: Invitation = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=400, detail="邀请码无效")
    if invite.status != "active":
        raise HTTPException(status_code=400, detail="邀请码已失效")
    if invite.use_count >= invite.max_uses:
        raise HTTPException(status_code=400, detail="邀请码已用尽")
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="邀请码已过期")

    # 检查用户名
    result2 = await db.execute(select(User).where(User.username == data.username))
    if result2.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=data.username,
        password=hash_password(data.password),
        email=data.email,
        role=data.role or invite.role,
        status="active"
    )
    db.add(user)
    await db.flush()

    # 消耗邀请码
    invite.use_count += 1
    invite.used_by = user.id
    invite.used_at = datetime.utcnow()
    if invite.use_count >= invite.max_uses:
        invite.status = "used"

    await db.commit()
    await db.refresh(user)
    return UserOut(
        id=user.id, username=user.username, role=user.role,
        email=user.email, status=user.status, created_at=str(user.created_at)
    )

# ── 邀请码管理（仅管理员） ──
@router.post("/invites", response_model=InviteCodeOut)
async def create_invite_code(
    data: InviteCodeCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """生成邀请码"""
    code = secrets.token_urlsafe(12)
    expires_at = datetime.utcnow() + timedelta(days=data.expires_in_days) if data.expires_in_days > 0 else None

    invite = Invitation(
        code=code,
        created_by=admin.id,
        role=data.role,
        max_uses=data.max_uses,
        expires_at=expires_at,
        status="active"
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return InviteCodeOut(
        id=invite.id, code=invite.code, role=invite.role,
        max_uses=invite.max_uses, use_count=invite.use_count,
        expires_at=str(invite.expires_at) if invite.expires_at else None,
        status=invite.status, created_at=str(invite.created_at)
    )

@router.get("/invites", response_model=InviteCodeList)
async def list_invite_codes(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """列出所有邀请码（仅管理员）"""
    result = await db.execute(select(Invitation).order_by(Invitation.created_at.desc()))
    invites = result.scalars().all()
    total = len(invites)
    codes = [
        InviteCodeOut(
            id=i.id, code=i.code, role=i.role,
            max_uses=i.max_uses, use_count=i.use_count,
            expires_at=str(i.expires_at) if i.expires_at else None,
            status=i.status, created_at=str(i.created_at)
        )
        for i in invites
    ]
    return InviteCodeList(total=total, codes=codes)

@router.delete("/invites/{code}")
async def delete_invite_code(
    code: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除邀请码"""
    result = await db.execute(select(Invitation).where(Invitation.code == code))
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="邀请码不存在")
    await db.delete(invite)
    await db.commit()
    return {"message": "邀请码已删除"}

# ── 登录 ──
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
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
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def get_me(current: User = Depends(get_current_user)):
    return UserOut(
        id=current.id, username=current.username, role=current.role,
        email=current.email, status=current.status, created_at=str(current.created_at)
    )
