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

# متغیرهای قابل استفاده در هر متن — به ادمین در ویرایشگر نمایش داده می‌شود
TEXT_VARIABLES: dict[str, tuple[str, ...]] = {
    "text_welcome": ("name", "gem", "lock", "bolt"),
    "text_welcome_referral": ("name", "referrer", "bonus"),
    "text_my_services": (),
    "text_my_services_empty": (),
    "text_service_item": ("order_id", "product_name", "expires", "status"),
    "text_service_config": ("config",),
    "text_wallet_title": ("balance",),
    "text_buy_success": ("order_id",),
    "text_test_used": (),
    "text_test_success": (),
    "text_referral_title": ("bonus", "link", "count", "total_bonus"),
    "text_tutorial_title": (),
    "text_support_ticket_open": ("ticket_id",),
    "text_insufficient_balance": ("balance", "price"),
    "text_banned": (),
    "text_card_transfer_approved": ("amount",),
}

# تلگرام حداکثر ۴۰۹۶ کاراکتر «مرئی» می‌پذیرد؛ ۹۶ کاراکتر حاشیه امن می‌گذاریم
MAX_VISIBLE_LEN = 4000

import re as _re

_TAG_RE = _re.compile(r"(<[^>]+>)")  # گروه capture: split تگ‌ها را هم برمی‌گرداند


def visible_len(html_text: str) -> int:
    """
    طول مرئی متن HTML به روش تلگرام: تگ‌ها حذف می‌شوند و
    طول متن باقی‌مانده بر حسب واحد UTF-16 شمرده می‌شود (هر ایموجی = ۲).
    """
    plain = _TAG_RE.sub("", html_text or "")
    return len(plain.encode("utf-16-le")) // 2


def split_html_message(html_text: str, limit: int = MAX_VISIBLE_LEN) -> list[str]:
    """
    متن HTML بلند را به چند قطعه ≤ limit تقسیم می‌کند.
    تگ‌ها هرگز وسطشان بریده نمی‌شوند (طول مرئی صفر دارند) و تگ‌های
    باز در ابتدای هر قطعه دوباره باز می‌شوند تا HTML معتبر بماند.
    """
    if visible_len(html_text) <= limit:
        return [html_text]

    def _open_tags_html(tags: list[str]) -> str:
        return "".join(f"<{t}>" for t in tags)

    chunks: list[str] = []
    current = ""          # متن مرئیِ انباشته‌ی قطعه فعلی
    open_tags: list[str] = []

    def _close_open() -> str:
        return "".join(f"</{t}>" for t in reversed(open_tags))

    def _flush():
        nonlocal current
        if not current:
            return
        chunks.append(current + _close_open())
        current = ""

    for tok in _TAG_RE.split(html_text):
        if not tok:
            continue

        if _TAG_RE.fullmatch(tok):
            # ── تگ ── طول مرئی صفر؛ همیشه جا می‌شود
            if tok.startswith("</"):
                name = tok[2:-1].strip()
                if name in open_tags:
                    while open_tags and open_tags.pop() != name:
                        pass
                current += tok
            elif tok.endswith("/>"):
                current += tok
            else:
                name = tok[1:-1].split()[0]
                open_tags.append(name)
                current += tok
            continue

        # ── متن ── ممکن است سرریز کند
        cur_len = visible_len(current)
        tok_len = visible_len(tok)
        room = limit - cur_len

        if tok_len <= room:
            current += tok
            continue

        # تقسیم متن روی مرز UTF-16
        pos = 0
        acc = 0
        for ch in tok:
            ch_len = 2 if ord(ch) > 0xFFFF else 1
            if acc + ch_len > room:
                break
            acc += ch_len
            pos += 1

        current += tok[:pos]
        _flush()
        rest = tok[pos:]
        # در قطعه‌ی جدید تگ‌های باز دوباره باز می‌شوند؛ room تازه
        while rest:
            prefix = _open_tags_html(open_tags)
            room2 = limit - visible_len(prefix)
            pos2 = 0
            acc2 = 0
            for ch in rest:
                ch_len = 2 if ord(ch) > 0xFFFF else 1
                if acc2 + ch_len > room2:
                    break
                acc2 += ch_len
                pos2 += 1
            current = prefix + rest[:pos2]
            rest = rest[pos2:]
            if rest:
                _flush()
                if pos2 == 0:
                    # ایموجی تنها از limit بلندتر است — ناچار برش وسطش
                    current = rest[: limit // 2]
                    rest = rest[limit // 2:]
                    _flush()

    _flush()
    return chunks


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


async def t_split(key: str, **kwargs) -> list[str]:
    """
    مثل t() ولی متن نهایی را به چند قطعه ≤ ۴۰۰۰ کاراکتر تقسیم می‌کند.
    برای متن‌هایی که می‌توانند بلند شوند (آموزش، سرویس‌های من و ...).
    هندلر باید هر قطعه را جداگانه بفرستد.
    """
    body = await t(key, **kwargs)
    return split_html_message(body)
