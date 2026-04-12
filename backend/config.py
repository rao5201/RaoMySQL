"""应用配置"""
import os
import warnings
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

# ⚠️  安全警告：以下为本地开发默认密钥
# 生产部署时必须在 .env 中设置真实的 SECRET_KEY / ENCRYPTION_KEY
_DEV_SECRET = "rao-dev-only-change-this-in-production-please-set-real-key"
_DEV_ENCRYPTION = "dev-encryption-key-do-not-use-prod"

class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "RaoMySQL"
    DEBUG: bool = True
    SECRET_KEY: str = os.getenv("SECRET_KEY", _DEV_SECRET)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # 数据库
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/raomysql.db"

    # 加密密钥（生产环境务必修改）
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", _DEV_ENCRYPTION)

    # CORS（逗号分隔，留空则仅允许同源）
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    # AI 配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o")

    # 备份存储路径
    BACKUP_DIR: Path = BASE_DIR / "backups"

    # SMTP 邮件配置
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587") or "587")
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")

    # 注册模式配置
    ALLOW_REGISTRATION: bool = os.getenv("ALLOW_REGISTRATION", "true").lower() == "true"
    INVITE_REQUIRED: bool = os.getenv("INVITE_REQUIRED", "false").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "allow"

    @property
    def cors_origins_list(self) -> list[str]:
        """返回 CORS 允许来源列表"""
        if not self.CORS_ORIGINS.strip():
            origins = ["http://localhost:3000", "http://localhost:8000"]
            if self.DEBUG:
                origins.append("*")
            return origins
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_dev_key(self) -> bool:
        return self.SECRET_KEY == _DEV_SECRET or len(self.SECRET_KEY) < 32

    def check_security(self):
        """启动时安全检查"""
        if not self.DEBUG:
            if self.is_dev_key:
                raise ValueError("⚠️  生产模式必须设置真实的 SECRET_KEY！")
            if self.ENCRYPTION_KEY == _DEV_ENCRYPTION or len(self.ENCRYPTION_KEY) < 16:
                raise ValueError("⚠️  生产模式必须设置真实的 ENCRYPTION_KEY！")
        elif self.is_dev_key:
            warnings.warn(
                "⚠️  使用默认开发密钥！请在生产环境设置真实的 SECRET_KEY",
                UserWarning, stacklevel=2
            )

settings = Settings()

# 启动时安全检查（仅警告，不阻止开发）
settings.check_security()
