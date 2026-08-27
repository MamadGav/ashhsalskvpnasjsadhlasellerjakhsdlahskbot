"""
محاسبه قیمت بر اساس تنظیمات
"""
from decimal import Decimal
from sqlalchemy import select
from database.engine import async_session
from database.models import BotSettings


DURATIONS = [7, 10, 20, 30]


async def get_settings() -> dict:
    async with async_session() as session:
        result = await session.execute(select(BotSettings))
        rows = result.scalars().all()
    return {s.key: s.value for s in rows}


async def calc_custom_price(data_gb: int, duration: int) -> Decimal:
    """قیمت سفارشی: (حجم × قیمت هر گیگ) - تخفیف روز"""
    settings = await get_settings()
    price_per_gb = Decimal(settings.get("price_per_gb", "4500"))
    dur_key = f"dur_{duration}_discount"
    discount = Decimal(settings.get(dur_key, "0"))
    base = price_per_gb * Decimal(str(data_gb))
    return max(base - discount, Decimal("0"))


async def calc_preset_price(product_price: Decimal, duration: int) -> Decimal:
    """قیمت پلن پیش‌فرض: قیمت پایه (۳۰ روزه) منهای تخفیف روز"""
    settings = await get_settings()
    if duration == 30:
        return product_price
    dur_key = f"dur_{duration}_discount"
    discount = Decimal(settings.get(dur_key, "0"))
    return max(product_price - discount, Decimal("0"))
