"""
⚙️ تنظیمات ربات تلگرام VPN
همه مقادیر از متغیرهای محیطی (Railway Variables) خوانده می‌شوند
"""
import os

# 🔑 توکن ربات تلگرام (از Railway Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# 👑 آیدی عددی ادمین‌ها (با کاما جدا کنید)
_admin_str = os.getenv("ADMIN_IDS", "7639233604,969253435")
DEFAULT_ADMIN_IDS = [int(x.strip()) for x in _admin_str.split(",") if x.strip()]

# 💳 شماره کارت
DEFAULT_CARD_NUMBER = os.getenv("CARD_NUMBER", "6104337812345678")

# 👤 نام صاحب کارت
DEFAULT_CARD_HOLDER = os.getenv("CARD_HOLDER", "غلام رضا ")

# 💰 مبلغ بونس دعوت دوستان (تومان) - پیش‌فرض از env
DEFAULT_REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", "5000"))

# 🧪 مدت اکانت تست رایگان (روز) - پیش‌فرض از env
DEFAULT_FREE_TEST_DAYS = int(os.getenv("FREE_TEST_DAYS", "3"))


async def get_referral_bonus() -> int:
    """دریافت بونس رفرال از دیتابیس"""
    from utils.pricing import get_settings
    settings = await get_settings()
    return int(settings.get("referral_bonus", str(DEFAULT_REFERRAL_BONUS)))


async def get_free_test_days() -> int:
    """دریافت روزهای تست رایگان از دیتابیس"""
    from utils.pricing import get_settings
    settings = await get_settings()
    return int(settings.get("free_test_days", str(DEFAULT_FREE_TEST_DAYS)))


async def get_admin_ids() -> list[int]:
    """دریافت لیست ادمین‌ها از دیتابیس"""
    from utils.pricing import get_settings
    settings = await get_settings()
    admin_str = settings.get("admin_ids", "")
    if admin_str:
        return [int(x.strip()) for x in admin_str.split(",") if x.strip()]
    return DEFAULT_ADMIN_IDS.copy()


async def is_admin(user_id: int) -> bool:
    """بررسی ادمین بودن کاربر"""
    admin_ids = await get_admin_ids()
    return user_id in admin_ids


async def add_admin(user_id: int) -> bool:
    """افزودن ادمین جدید"""
    from utils.pricing import get_settings
    from database.engine import async_session
    from database.models import BotSettings
    from sqlalchemy import select

    settings = await get_settings()
    admin_str = settings.get("admin_ids", "")
    current = [int(x.strip()) for x in admin_str.split(",") if x.strip()] if admin_str else DEFAULT_ADMIN_IDS.copy()

    if user_id in current:
        return False

    current.append(user_id)
    new_value = ",".join(str(x) for x in current)

    async with async_session() as session:
        setting = (await session.execute(
            select(BotSettings).where(BotSettings.key == "admin_ids")
        )).scalar_one_or_none()

        if setting:
            setting.value = new_value
        else:
            session.add(BotSettings(key="admin_ids", value=new_value))

        await session.commit()
    return True


async def remove_admin(user_id: int) -> bool:
    """حذف ادمین"""
    from utils.pricing import get_settings
    from database.engine import async_session
    from database.models import BotSettings
    from sqlalchemy import select

    settings = await get_settings()
    admin_str = settings.get("admin_ids", "")
    current = [int(x.strip()) for x in admin_str.split(",") if x.strip()] if admin_str else DEFAULT_ADMIN_IDS.copy()

    if user_id not in current:
        return False

    current.remove(user_id)
    new_value = ",".join(str(x) for x in current)

    async with async_session() as session:
        setting = (await session.execute(
            select(BotSettings).where(BotSettings.key == "admin_ids")
        )).scalar_one_or_none()

        if setting:
            setting.value = new_value
        else:
            session.add(BotSettings(key="admin_ids", value=new_value))

        await session.commit()
    return True


async def get_card_info() -> tuple[str, str]:
    """دریافت شماره کارت و نام صاحب از دیتابیس"""
    from utils.pricing import get_settings
    settings = await get_settings()
    card_number = settings.get("card_number", DEFAULT_CARD_NUMBER)
    card_holder = settings.get("card_holder", DEFAULT_CARD_HOLDER)
    return card_number, card_holder


async def set_card_info(card_number: str, card_holder: str):
    """ذخیره شماره کارت و نام صاحب"""
    from database.engine import async_session
    from database.models import BotSettings
    from sqlalchemy import select

    async with async_session() as session:
        for key, value in [("card_number", card_number), ("card_holder", card_holder)]:
            setting = (await session.execute(
                select(BotSettings).where(BotSettings.key == key)
            )).scalar_one_or_none()

            if setting:
                setting.value = value
            else:
                session.add(BotSettings(key=key, value=value))

        await session.commit()
