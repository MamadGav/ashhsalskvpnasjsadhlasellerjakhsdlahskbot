"""
📝 مدیریت متن‌های ربات از دیتابیس
------------------------------------------------
ادمین می‌تواند هر متنی را از پنل ادمین ویرایش کند.
ایموجی‌های پرمیوم ارسالی ادمین به‌صورت خودکار به تگ HTML
تبدیل و ذخیره می‌شوند (شامل <tg-emoji> و <b> و <i> و ...).
"""
from html import escape as _html_escape

from database.engine import async_session
from database.models import BotSettings
from sqlalchemy import select


def esc(value) -> str:
    """escape مقدار داینامیک برای ارسال در پیام HTML (لینک کانفیگ، نام کاربر و ...)"""
    return _html_escape(str(value), quote=False)

# کلیدهای متن قابل ویرایش: کلید دیتابیس = (کلید TEXTS، عنوان فارسی)
EDITABLE_TEXTS: dict[str, tuple[str, str]] = {
    "text_welcome": ("welcome", "پیام خوش‌آمدگویی"),
    "text_welcome_referral": ("welcome_referral", "پیام خوش‌آمد دعوت‌شده"),
    "text_my_services": ("my_services", "عنوان سرویس‌های من"),
    "text_my_services_empty": ("my_services_empty", "پیام «سرویس ندارید»"),
    "text_service_item": ("service_item", "قالب هر سرویس"),
    "text_service_config": ("service_config", "قالب لینک کانفیگ"),
    "text_wallet_title": ("wallet_title", "عنوان کیف پول"),
    "text_buy_success": ("buy_success", "پیام ثبت سفارش موفق"),
    "text_test_used": ("test_used", "پیام «تست استفاده شده»"),
    "text_test_success": ("test_success", "پیام فعال‌سازی تست"),
    "text_referral_title": ("referral_title", "صفحه دعوت از دوستان"),
    "text_tutorial_title": ("tutorial_title", "متن آموزش استفاده"),
    "text_support_ticket_open": ("support_ticket_open", "پیام باز شدن تیکت"),
    "text_insufficient_balance": ("insufficient_balance", "پیام موجودی ناکافی"),
    "text_banned": ("banned", "پیام کاربر مسدود"),
    "text_card_transfer_approved": ("card_transfer_approved", "پیام تایید کارت به کارت"),
}


_cache: dict[str, str] = {}
_loaded = False


async def _load_cache():
    global _loaded
    async with async_session() as session:
        result = await session.execute(
            select(BotSettings).where(BotSettings.key.like("text_%"))
        )
        for s in result.scalars().all():
            _cache[s.key] = s.value
    _loaded = True


async def get_custom_text(key: str) -> str | None:
    """خواندن متن سفارشی از کش (بار اول از دیتابیس)"""
    if not _loaded:
        await _load_cache()
    return _cache.get(key)


async def set_custom_text(key: str, value: str):
    """ذخیره متن سفارشی در دیتابیس و کش"""
    async with async_session() as session:
        setting = (await session.execute(
            select(BotSettings).where(BotSettings.key == key)
        )).scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            session.add(BotSettings(key=key, value=value))
        await session.commit()
    _cache[key] = value


async def invalidate_cache():
    """خالی کردن کش (در صورت نیاز)"""
    global _loaded
    _cache.clear()
    _loaded = False


async def t(key: str, **kwargs) -> str:
    """
    گرفتن متن نهایی (async): اول متن سفارشی ادمین، بعد پیش‌فرض.
    پارامترها (مثل name، order_id) روی هر دو اعمال می‌شوند.
    """
    from locales.fa import TEXTS

    # متن خالی (بعد از reset) یعنی «پیش‌فرض»
    custom = await get_custom_text(f"text_{key}")
    template = custom if custom else TEXTS.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError, AttributeError):
            # اگر قالب ادمین خراب بود، پیش‌فرض را نشان بده
            if custom:
                try:
                    return TEXTS.get(key, key).format(**kwargs)
                except Exception:
                    return TEXTS.get(key, key)
            return template
    return template
