"""应用配置"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "RaoMySQL"
    DEBUG: bool = True
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    # 数据库
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/raomysql.db"
    
    # 加密密钥（生产环境务必修改）
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "32-byte-encryption-key-here!!")
    
    # AI 配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o")
    
    # 备份存储路径
    BACKUP_DIR: Path = BASE_DIR / "backups"
    
    # SMTP 邮件配置
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")

    # 注册模式配置
    ALLOW_REGISTRATION: bool = os.getenv("ALLOW_REGISTRATION", "true").lower() == "true"
    INVITE_REQUIRED: bool = os.getenv("INVITE_REQUIRED", "false").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
