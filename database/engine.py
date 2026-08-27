from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

# ساخت پوشه data اگر وجود نداشت
os.makedirs("data", exist_ok=True)

DB_URL = "sqlite+aiosqlite:///data/bot.db"
engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """ساخت جداول دیتابیس در صورت عدم وجود"""
    async with engine.begin() as conn:
        from database.models import Base
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
