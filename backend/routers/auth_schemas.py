"""认证相关 Pydantic 模型"""
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "developer"

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[str]
    status: str
    created_at: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None

# ── 邀请码相关 ──
class InviteCodeCreate(BaseModel):
    role: str = "developer"
    max_uses: int = 1
    expires_in_days: int = 7

class InviteCodeOut(BaseModel):
    id: int
    code: str
    role: str
    max_uses: int
    use_count: int
    expires_at: Optional[str]
    status: str
    created_at: str

    class Config:
        from_attributes = True

class InviteCodeList(BaseModel):
    total: int
    codes: list[InviteCodeOut]

class RegisterWithInvite(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "developer"
    invite_code: str
