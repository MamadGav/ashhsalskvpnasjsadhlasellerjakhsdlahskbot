"""
🎨 ایموجی‌های پرمیوم (Custom Emoji)
------------------------------------------------
برای فعال‌سازی:
1. آیدی ایموجی‌های پرمیوم مورد نظر را از @JSONDumpBot بگیرید
   (یک پیام با ایموجی پرمیوم بفرست → Reply → آیدی مثل 5368324170671202286)
2. مقدار هر کلید را در EMOJI پر کنید
3. اگر مقدار خالی باشد، ایموجی معمولی (fallback) نمایش داده می‌شود

⚠️ پیش‌نیاز: صاحب بات باید Telegram Premium داشته باشد
   (یا بات نام کاربری از fragment.com خریده باشد)
"""

# کلید = نام، مقدار = custom_emoji_id (خالی = استفاده از fallback)
EMOJI: dict[str, str] = {
    # منوی اصلی
    "cart": "5971865890071779232",           # 🛒 خرید سرویس
    "test": "5971950346308688754",           # 🧪 اکانت تست
    "package": "5116648080787112958",        # 📦 سرویس‌ها
    "wallet": "5974286598064315115",         # 💰 کیف پول
    "referral": "",       # 👥 دعوت
    "book": "",           # 📖 آموزش
    "support": "",        # 📞 پشتیبانی
    "back": "",           # 🔙 بازگشت
    # پنل ادمین
    "crown": "",          # 👑 ادمین
    "chart": "",          # 📊 داشبورد
    "orders": "",         # 📋 سفارشات
    "products": "",       # 📦 پلن‌ها
    "users": "",          # 👥 کاربران
    "card": "",           # 💳 کارت
    "ticket": "",         # 🎫 تیکت
    "discount": "",       # 🏷️ تخفیف
    "settings": "",       # ⚙️ تنظیمات
    "plus": "",           # ➕ افزودن
    "minus": "",          # ➖ حذف
    "check": "",          # ✅ تایید
    "cross": "",          # ❌ رد/انصراف
    "ban": "",            # 🚫 مسدود
    "edit": "",           # ✏️ ویرایش
    "delete": "",         # 🗑️ حذف
    "refresh": "",        # 🔄 وضعیت
    # تزئینی
    "gem": "",            # 💎 تزئین عنوان
    "bolt": "",           # ⚡ سرعت
    "lock": "",           # 🔒 امنیت
    "fire": "",           # 🔥 داغ
    "sparkles": "",       # ✨ تزئین
    "star": "",           # ⭐ امتیاز
    "rocket": "",         # 🚀 شروع
}

# ایموجی fallback برای هر کلید (وقتی آیدی پرمیوم خالی است)
FALLBACK: dict[str, str] = {
    "cart": "🛒", "test": "🧪", "package": "📦", "wallet": "💰",
    "referral": "👥", "book": "📖", "support": "📞", "back": "🔙",
    "crown": "👑", "chart": "📊", "orders": "📋", "products": "📦",
    "users": "👥", "card": "💳", "ticket": "🎫", "discount": "🏷️",
    "settings": "⚙️", "plus": "➕", "minus": "➖", "check": "✅",
    "cross": "❌", "ban": "🚫", "edit": "✏️", "delete": "🗑️",
    "refresh": "🔄", "gem": "💎", "bolt": "⚡", "lock": "🔒",
    "fire": "🔥", "sparkles": "✨", "star": "⭐", "rocket": "🚀",
}


def emoji_id(key: str) -> str | None:
    """آیدی ایموجی پرمیوم؛ اگر خالی باشد None برمی‌گرداند"""
    return EMOJI.get(key) or None


def tg(key: str) -> str:
    """
    تگ HTML ایموجی پرمیوم برای متن پیام.
    اگر آیدی خالی باشد، همان ایموجی معمولی برمی‌گرداند.

    استفاده:  f"سلام {tg('gem')} خوش آمدید"
    """
    eid = EMOJI.get(key)
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{FALLBACK.get(key, "•")}</tg-emoji>'
    return FALLBACK.get(key, "•")


def kb(key: str) -> str | None:
    """مقدار icon_custom_emoji_id برای دکمه کیبورد؛ None یعنی بدون آیکون"""
    return emoji_id(key)
