from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.icons import kb as _icon, tg

# Style constants for button colors
STYLE_PRIMARY = "primary"    # آبی - اکشن‌های اصلی و ناوبری
STYLE_SUCCESS = "success"    # سبز - تایید، موفقیت
STYLE_DANGER = "danger"      # قرمز - حذف، رد، خطر


def btn(text: str, callback_data: str, style: str | None = None, icon: str | None = None):
    """ساخت دکمه با پشتیبانی آیکون پرمیوم (اگر آیدی تنظیم شده باشد)"""
    return dict(
        text=text,
        callback_data=callback_data,
        style=style,
        icon_custom_emoji_id=_icon(icon) if icon else None,
    )


def main_menu_kb() -> InlineKeyboardMarkup:
    buttons = [
        (btn("خرید سرویس جدید", "buy", STYLE_PRIMARY, "cart"),),
        (btn("اکانت تست رایگان", "test_account", STYLE_SUCCESS, "test"),),
        (btn("سرویس‌های من", "my_services", None, "package"),
         btn("کیف پول من", "wallet", None, "wallet")),
        (btn("دعوت از دوستان", "referral", None, "referral"),
         btn("آموزش استفاده", "tutorial", None, "book")),
        (btn("پشتیبانی", "support", None, "support"),),
    ]
    kb = InlineKeyboardBuilder()
    for row in buttons:
        for b in row:
            kb.button(**b)
    kb.adjust(2)
    return kb.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("بازگشت به منو", "menu", STYLE_PRIMARY, "back"))
    return kb.as_markup()


def wallet_methods_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("کارت به کارت", "wallet_card", STYLE_PRIMARY, "card"))
    kb.button(**btn("بازگشت", "menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def products_list_kb(products: list) -> InlineKeyboardMarkup:
    """لیست پلن‌های پیش‌فرض"""
    kb = InlineKeyboardBuilder()
    for p in products:
        label = f"📦 {p.name} - {p.price:,.0f} تومان"
        kb.button(text=label, callback_data=f"product_{p.id}")
    kb.button(**btn("حجم دلخواه", "custom_plan", STYLE_PRIMARY, "edit"))
    kb.button(**btn("بازگشت", "menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def duration_kb(product_id: int) -> InlineKeyboardMarkup:
    """انتخاب مدت برای پلن پیش‌فرض"""
    kb = InlineKeyboardBuilder()
    kb.button(**btn("⚡ ۷ روزه (-۶,۰۰۰ تومان)", f"dur_{product_id}_7", STYLE_SUCCESS))
    kb.button(**btn("📦 ۳۰ روزه (قیمت پایه)", f"dur_{product_id}_30", STYLE_PRIMARY))
    kb.button(**btn("انصراف", "menu", STYLE_DANGER, "cross"))
    kb.adjust(1)
    return kb.as_markup()


def custom_plan_gb_kb() -> InlineKeyboardMarkup:
    """انتخاب حجم دلخواه"""
    kb = InlineKeyboardBuilder()
    for gb in [7, 10, 15, 20, 25, 30, 40, 50, 60]:
        kb.button(text=f"📊 {gb} گیگ", callback_data=f"cgb_{gb}")
    kb.button(**btn("مقدار دلخواه", "cgb_custom", STYLE_PRIMARY, "edit"))
    kb.button(**btn("انصراف", "menu", STYLE_DANGER, "cross"))
    kb.adjust(3)
    return kb.as_markup()


def custom_plan_duration_kb(data_gb: int) -> InlineKeyboardMarkup:
    """انتخاب مدت برای حجم دلخواه"""
    kb = InlineKeyboardBuilder()
    for d in [7, 10, 20, 30]:
        kb.button(**btn(f"⏰ {d} روزه", f"cdur_{data_gb}_{d}", STYLE_SUCCESS))
    kb.button(**btn("انصراف", "menu", STYLE_DANGER, "cross"))
    kb.adjust(2)
    return kb.as_markup()


def payment_choice_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("پرداخت از کیف پول", "pay_wallet", STYLE_SUCCESS, "wallet"))
    kb.button(**btn("کارت به کارت", "pay_card", STYLE_PRIMARY, "card"))
    kb.button(**btn("انصراف", "menu", STYLE_DANGER, "cross"))
    kb.adjust(1)
    return kb.as_markup()


def confirm_buy_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("تایید و پرداخت", "confirm_buy", STYLE_SUCCESS, "check"))
    kb.button(**btn("انصراف", "menu", STYLE_DANGER, "cross"))
    kb.adjust(1)
    return kb.as_markup()


def discount_skip_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("ادامه بدون کد تخفیف", "skip_discount", STYLE_PRIMARY))
    kb.button(**btn("انصراف", "menu", STYLE_DANGER, "cross"))
    kb.adjust(1)
    return kb.as_markup()


# ===================== ADMIN =====================

def admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("داشبورد", "admin_dashboard", STYLE_PRIMARY, "chart"))
    kb.button(**btn("سفارشات در انتظار", "admin_pending_orders", STYLE_SUCCESS, "orders"))
    kb.button(**btn("مدیریت پلن‌ها", "admin_products", None, "products"))
    kb.button(**btn("مدیریت کاربران", "admin_users", None, "users"))
    kb.button(**btn("تایید کارت به کارت", "admin_card_transfers", None, "card"))
    kb.button(**btn("تیکت‌ها", "admin_tickets", None, "ticket"))
    kb.button(**btn("کد تخفیف", "admin_discounts", None, "discount"))
    kb.button(**btn("تنظیمات قیمت‌گذاری", "admin_settings", None, "settings"))
    kb.button(**btn("ویرایش متن‌ها", "admin_texts", None, "edit"))
    kb.button(**btn("مدیریت ادمین‌ها", "admin_manage_admins", None, "crown"))
    kb.adjust(1)
    return kb.as_markup()


def admin_orders_list_kb(orders: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for item in orders:
        o = item["order"]
        user = item.get("user")
        uname = (user.first_name or "نامشخص") if user else "نامشخص"
        kb.button(
            text=f"📋 #{o.id} | {uname} | {o.final_price:,.0f}t",
            callback_data=f"admin_view_order_{o.id}"
        )
    kb.button(**btn("بازگشت", "admin_menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_order_detail_kb(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("تایید و ارسال کانفیگ", f"admin_approve_{order_id}", STYLE_SUCCESS, "check"))
    kb.button(**btn("رد سفارش", f"admin_reject_{order_id}", STYLE_DANGER, "cross"))
    kb.button(**btn("بازگشت به لیست", "admin_pending_orders", STYLE_PRIMARY, "back"))
    kb.button(**btn("پنل ادمین", "admin_menu", STYLE_PRIMARY, "crown"))
    kb.adjust(1)
    return kb.as_markup()


def admin_card_list_kb(payments: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for p in payments:
        user = p.get("user")
        pay = p.get("payment")
        uname = (user.first_name or "نامشخص") if user else "نامشخص"
        kb.button(
            text=f"⇜ #{pay.id} | {uname} | {pay.amount:,.0f}t",
            callback_data=f"admin_view_card_{pay.id}"
        )
    kb.button(**btn("بازگشت", "admin_menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_card_detail_kb(payment_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("تایید و شارژ کیف پول", f"admin_accept_card_{payment_id}", STYLE_SUCCESS, "check"))
    kb.button(**btn("رد تراکنش", f"admin_reject_card_{payment_id}", STYLE_DANGER, "cross"))
    kb.button(**btn("بازگشت", "admin_card_transfers", STYLE_PRIMARY, "back"))
    kb.button(**btn("پنل ادمین", "admin_menu", STYLE_PRIMARY, "crown"))
    kb.adjust(1)
    return kb.as_markup()


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for p in products:
        s = "✅" if p.is_active else "❌"
        kb.button(text=f"{s} {p.name} | {p.price:,.0f}t", callback_data=f"admin_view_prod_{p.id}")
    kb.button(**btn("افزودن پلن", "admin_add_product", STYLE_SUCCESS, "plus"))
    kb.button(**btn("بازگشت", "admin_menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_product_type_kb() -> InlineKeyboardMarkup:
    """انتخاب نوع پلن هنگام ساخت (فروش/تست)"""
    kb = InlineKeyboardBuilder()
    kb.button(**btn("پلن فروش", "prodtype_sell", STYLE_PRIMARY, "cart"))
    kb.button(**btn("پلن تست", "prodtype_test", STYLE_SUCCESS, "test"))
    kb.button(**btn("بازگشت به پنل ادمین", "admin_menu", STYLE_DANGER, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_product_edit_kb(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("نام", f"edit_prod_name_{product_id}", None, "edit"))
    kb.button(**btn("حجم (GB)", f"edit_prod_data_{product_id}", None, "edit"))
    kb.button(**btn("قیمت پایه", f"edit_prod_price_{product_id}", None, "edit"))
    kb.button(**btn("توضیحات", f"edit_prod_desc_{product_id}", None, "edit"))
    kb.button(**btn("وضعیت", f"admin_toggle_prod_{product_id}", STYLE_PRIMARY, "refresh"))
    kb.button(**btn("حذف", f"admin_delete_prod_{product_id}", STYLE_DANGER, "delete"))
    kb.button(**btn("بازگشت", "admin_products", STYLE_PRIMARY, "back"))
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def admin_user_edit_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("مسدود/رفع", f"admin_toggle_ban_{user_id}", STYLE_DANGER, "ban"))
    kb.button(**btn("ادمین", f"admin_toggle_admin_{user_id}", STYLE_PRIMARY, "crown"))
    kb.button(**btn("شارژ کیف پول", f"admin_charge_wallet_{user_id}", STYLE_SUCCESS, "wallet"))
    kb.button(**btn("بازگشت", "admin_users", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def back_to_admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("بازگشت به پنل ادمین", "admin_menu", STYLE_PRIMARY, "back"))
    return kb.as_markup()


def admin_support_reply_kb(ticket_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn(f"پاسخ به تیکت #{ticket_id}", f"admin_reply_ticket_{ticket_id}", STYLE_PRIMARY, "ticket"))
    kb.button(**btn("بستن تیکت", f"admin_close_ticket_{ticket_id}", STYLE_SUCCESS, "check"))
    kb.button(**btn("بازگشت", "admin_menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_discounts_kb(codes: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in codes:
        s = "✅" if c.is_active else "❌"
        limit = f"{c.used_count}/{c.max_uses}" if c.max_uses > 0 else f"{c.used_count}/∞"
        kb.button(text=f"{s} {c.code} ({c.percent}% | {limit})", callback_data=f"admin_view_disc_{c.id}")
    kb.button(**btn("کد جدید", "admin_add_discount", STYLE_SUCCESS, "plus"))
    kb.button(**btn("بازگشت", "admin_menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_discount_detail_kb(code_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("وضعیت", f"admin_toggle_disc_{code_id}", STYLE_PRIMARY, "refresh"))
    kb.button(**btn("حذف", f"admin_delete_disc_{code_id}", STYLE_DANGER, "delete"))
    kb.button(**btn("بازگشت", "admin_discounts", STYLE_PRIMARY, "back"))
    kb.button(**btn("پنل ادمین", "admin_menu", STYLE_PRIMARY, "crown"))
    kb.adjust(1)
    return kb.as_markup()


def admin_manage_admins_kb() -> InlineKeyboardMarkup:
    """کیبورد مدیریت ادمین‌ها"""
    kb = InlineKeyboardBuilder()
    kb.button(**btn("افزودن ادمین", "admin_add_admin", STYLE_SUCCESS, "plus"))
    kb.button(**btn("حذف ادمین", "admin_remove_admin_menu", STYLE_DANGER, "minus"))
    kb.button(**btn("بازگشت", "admin_menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_remove_admin_kb(admin_ids: list) -> InlineKeyboardMarkup:
    """لیست ادمین‌ها برای حذف"""
    kb = InlineKeyboardBuilder()
    for admin_id in admin_ids:
        kb.button(**btn(f"حذف {admin_id}", f"admin_remove_admin_{admin_id}", STYLE_DANGER, "delete"))
    kb.button(**btn("بازگشت", "admin_manage_admins", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_texts_kb() -> InlineKeyboardMarkup:
    """لیست متن‌های قابل ویرایش"""
    from utils.texts import EDITABLE_TEXTS
    kb = InlineKeyboardBuilder()
    for db_key, (_, label) in EDITABLE_TEXTS.items():
        kb.button(text=f"📝 {label}", callback_data=f"admin_edit_text_{db_key}")
    kb.button(**btn("بازگشت", "admin_menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_text_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("📝 ویرایش متن‌های دیگر", "admin_texts", STYLE_PRIMARY, "edit"))
    kb.button(**btn("پنل ادمین", "admin_menu", STYLE_PRIMARY, "crown"))
    kb.adjust(1)
    return kb.as_markup()


def admin_text_confirm_kb_custom(db_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(**btn("✏️ ویرایش این متن", f"admin_edit_text_{db_key}", STYLE_PRIMARY, "edit"))
    kb.button(**btn("👀 پیش‌نمایش نهایی", f"admin_preview_text_{db_key}", None, "check"))
    kb.button(**btn("بازگشت به لیست", "admin_texts", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()


def admin_settings_kb(settings: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    # قیمت‌گذاری
    kb.button(text=f"💰 قیمت هر گیگ: {settings.get('price_per_gb', '?')} تومان", callback_data="noop")
    kb.button(text=f"7 روز: -{settings.get('dur_7_discount', '?')} تومان", callback_data="noop")
    kb.button(text=f"10 روز: -{settings.get('dur_10_discount', '?')} تومان", callback_data="noop")
    kb.button(text=f"20 روز: -{settings.get('dur_20_discount', '?')} تومان", callback_data="noop")
    kb.button(text=f"30 روز: پایه (بدون تخفیف)", callback_data="noop")
    kb.button(**btn("تغییر قیمت هر گیگ", "edit_setting_price_per_gb", STYLE_PRIMARY, "edit"))
    kb.button(**btn("تغییر تخفیف ۷ روزه", "edit_setting_dur_7", STYLE_PRIMARY, "edit"))
    kb.button(**btn("تغییر تخفیف ۱۰ روزه", "edit_setting_dur_10", STYLE_PRIMARY, "edit"))
    kb.button(**btn("تغییر تخفیف ۲۰ روزه", "edit_setting_dur_20", STYLE_PRIMARY, "edit"))
    # تنظیمات عمومی
    kb.button(text=f"👥 بونس دعوت: {settings.get('referral_bonus', '5000')} تومان", callback_data="noop")
    kb.button(text=f"🧪 روز تست رایگان: {settings.get('free_test_days', '3')}", callback_data="noop")
    kb.button(**btn("تغییر شماره کارت", "admin_edit_card", STYLE_PRIMARY, "card"))
    kb.button(**btn("تغییر بونس دعوت", "edit_setting_referral_bonus", STYLE_PRIMARY, "edit"))
    kb.button(**btn("تغییر روز تست رایگان", "edit_setting_free_test_days", STYLE_PRIMARY, "edit"))
    kb.button(**btn("بازگشت", "admin_menu", STYLE_PRIMARY, "back"))
    kb.adjust(1)
    return kb.as_markup()
