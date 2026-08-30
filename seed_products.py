"""
ایجاد پلن‌های پیش‌فرض و تنظیمات اولیه
"""
import asyncio
from decimal import Decimal
from sqlalchemy import select
from database.engine import engine, async_session, init_db
from database.models import Product, BotSettings


PRESET_PLANS = [
    ("10 گیگ", 10, 30, Decimal("45000")),
    ("20 گیگ", 20, 30, Decimal("85000")),
    ("30 گیگ", 30, 30, Decimal("120000")),
    ("40 گیگ", 40, 30, Decimal("155000")),
    ("50 گیگ", 50, 30, Decimal("200000")),
    ("60 گیگ", 60, 30, Decimal("230000")),
]

TEST_PLAN = ("🧪 اکانت تست رایگان", 1, 3, Decimal("0"))

DEFAULT_SETTINGS = {
    "price_per_gb": "4500",              # تومان - قیمت هر گیگ (برای سفارشی)
    "dur_7_discount": "6000",            # کمتر از 30 روزه
    "dur_10_discount": "4000",
    "dur_20_discount": "2000",
    "dur_30_discount": "0",              # پایه
    "custom_min_gb": "7",
    "custom_max_gb": "100",
    "admin_ids": "7639233604,969253435", # ادمین‌های پیش‌فرض
    "card_number": "6104337812345678",   # شماره کارت پیش‌فرض
    "card_holder": "غلام رضا ",          # نام صاحب کارت پیش‌فرض
    "referral_bonus": "5000",           # بونس دعوت (تومان)
    "free_test_days": "3",              # روز تست رایگان
}


async def seed():
    await init_db()
    async with async_session() as session:
        # Seed products
        existing = (await session.execute(select(Product))).scalars().all()
        existing_names = {p.name for p in existing}
        added = 0
        for name, data_gb, duration, price in PRESET_PLANS:
            if name not in existing_names:
                session.add(Product(
                    name=name, data_gb=data_gb,
                    description=f"پلن {name} - {duration} روزه",
                    duration_days=duration, price=price,
                    is_active=True, is_test=False,
                ))
                added += 1

        # Seed test plan (is_test=True)
        test_name = TEST_PLAN[0]
        if test_name not in existing_names:
            session.add(Product(
                name=test_name, data_gb=TEST_PLAN[1],
                description="اکانت تست رایگان",
                duration_days=TEST_PLAN[2], price=TEST_PLAN[3],
                is_active=True, is_test=True,
            ))
            added += 1

        # Seed settings
        existing_settings = (await session.execute(select(BotSettings))).scalars().all()
        existing_keys = {s.key for s in existing_settings}
        for key, value in DEFAULT_SETTINGS.items():
            if key not in existing_keys:
                session.add(BotSettings(key=key, value=value))

        await session.commit()
        print(f"Done: {added} products added, settings initialized.")


if __name__ == "__main__":
    asyncio.run(seed())
