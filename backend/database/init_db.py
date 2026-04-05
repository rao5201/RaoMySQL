"""初始化 SQLite 数据库 + 提供 get_db 依赖"""
from database.models import Base
from config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"[RaoMySQL] 数据库初始化完成: {settings.DATABASE_URL}")

if __name__ == "__main__":
    asyncio.run(init_db())
