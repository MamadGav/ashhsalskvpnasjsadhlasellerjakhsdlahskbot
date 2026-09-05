from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

# دریافت URL دیتابیس از متغیر محیطی (برای Railway)
# اگر متغیر نباشد، از SQLite به صورت local استفاده می‌شود
DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    # PostgreSQL (Railway یا هاست ابری)
    # Railway ممکنه postgres:// بده که باید postgresql+asyncpg:// باشه
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    # SQLite (برای توسعه محلی)
    os.makedirs("data", exist_ok=True)
    DATABASE_URL = "sqlite+aiosqlite:///data/bot.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """ساخت جداول دیتابیس در صورت عدم وجود + مایگریشن خودکار ستون‌های قدیمی"""
    async with engine.begin() as conn:
        from database.models import Base
        await conn.run_sync(Base.metadata.create_all)

        # مایگریشن: ستون value جدول bot_settings از varchar(256) به TEXT
        # (create_all جدول موجود را تغییر نمی‌دهد — این کوئری idempotent است)
        from sqlalchemy import text as sql_text
        try:
            await conn.execute(sql_text("ALTER TABLE bot_settings ALTER COLUMN value TYPE TEXT"))
        except Exception:
            pass  # SQLite از این سینتکس پشتیبانی نمی‌کند و نیازی هم ندارد (Text همان TEXT است)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
