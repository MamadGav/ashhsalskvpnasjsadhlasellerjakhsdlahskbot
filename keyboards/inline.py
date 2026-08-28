from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    buttons = [
        ("🛒 خرید سرویس جدید", "buy"),
        ("🧪 اکانت تست رایگان", "test_account"),
        ("📦 سرویس‌های من", "my_services"),
        ("💰 کیف پول من", "wallet"),
        ("👥 دعوت از دوستان", "referral"),
        ("📖 آموزش استفاده", "tutorial"),
        ("📞 پشتیبانی", "support"),
    ]
    kb = InlineKeyboardBuilder()
    for text, cb in buttons:
        kb.button(text=text, callback_data=cb)
    kb.adjust(2)
    return kb.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 بازگشت به منو", callback_data="menu")
    return kb.as_markup()


def wallet_methods_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⇜ کارت به کارت", callback_data="wallet_card")
    kb.button(text="🔙 بازگشت", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def products_list_kb(products: list) -> InlineKeyboardMarkup:
    """لیست پلن‌های پیش‌فرض"""
    kb = InlineKeyboardBuilder()
    for p in products:
        label = f"📦 {p.name} - {p.price:,.0f} تومان"
        kb.button(text=label, callback_data=f"product_{p.id}")
    kb.button(text="✏️ حجم دلخواه", callback_data="custom_plan")
    kb.button(text="🔙 بازگشت", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def duration_kb(product_id: int) -> InlineKeyboardMarkup:
    """انتخاب مدت برای پلن پیش‌فرض"""
    kb = InlineKeyboardBuilder()
    kb.button(text="⚡ ۷ روزه (-۶,۰۰۰ تومان)", callback_data=f"dur_{product_id}_7")
    kb.button(text="📦 ۳۰ روزه (قیمت پایه)", callback_data=f"dur_{product_id}_30")
    kb.button(text="❌ انصراف", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def custom_plan_gb_kb() -> InlineKeyboardMarkup:
    """انتخاب حجم دلخواه"""
    kb = InlineKeyboardBuilder()
    for gb in [7, 10, 15, 20, 25, 30, 40, 50, 60]:
        kb.button(text=f"📊 {gb} گیگ", callback_data=f"cgb_{gb}")
    kb.button(text="⌨️ مقدار دلخواه", callback_data="cgb_custom")
    kb.button(text="❌ انصراف", callback_data="menu")
    kb.adjust(3)
    return kb.as_markup()


def custom_plan_duration_kb(data_gb: int) -> InlineKeyboardMarkup:
    """انتخاب مدت برای حجم دلخواه"""
    kb = InlineKeyboardBuilder()
    for d in [7, 10, 20, 30]:
        kb.button(text=f"⏰ {d} روزه", callback_data=f"cdur_{data_gb}_{d}")
    kb.button(text="❌ انصراف", callback_data="menu")
    kb.adjust(2)
    return kb.as_markup()


def payment_choice_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 پرداخت از کیف پول", callback_data="pay_wallet")
    kb.button(text="⇜ کارت به کارت", callback_data="pay_card")
    kb.button(text="❌ انصراف", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def confirm_buy_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ تایید و پرداخت", callback_data="confirm_buy")
    kb.button(text="❌ انصراف", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def discount_skip_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➡️ ادامه بدون کد تخفیف", callback_data="skip_discount")
    kb.button(text="❌ انصراف", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


# ===================== ADMIN =====================

def admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 داشبورد", callback_data="admin_dashboard")
    kb.button(text="📋 سفارشات در انتظار", callback_data="admin_pending_orders")
    kb.button(text="📦 مدیریت پلن‌ها", callback_data="admin_products")
    kb.button(text="👥 مدیریت کاربران", callback_data="admin_users")
    kb.button(text="⇜ تایید کارت به کارت", callback_data="admin_card_transfers")
    kb.button(text="🎫 تیکت‌ها", callback_data="admin_tickets")
    kb.button(text="🏷️ کد تخفیف", callback_data="admin_discounts")
    kb.button(text="⚙️ تنظیمات قیمت‌گذاری", callback_data="admin_settings")
    kb.button(text="👑 مدیریت ادمین‌ها", callback_data="admin_manage_admins")
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
    kb.button(text="🔙 بازگشت", callback_data="admin_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_order_detail_kb(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ تایید و ارسال کانفیگ", callback_data=f"admin_approve_{order_id}")
    kb.button(text="❌ رد سفارش", callback_data=f"admin_reject_{order_id}")
    kb.button(text="🔙 بازگشت به لیست", callback_data="admin_pending_orders")
    kb.button(text="🏠 پنل ادمین", callback_data="admin_menu")
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
    kb.button(text="🔙 بازگشت", callback_data="admin_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_card_detail_kb(payment_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ تایید و شارژ کیف پول", callback_data=f"admin_accept_card_{payment_id}")
    kb.button(text="❌ رد تراکنش", callback_data=f"admin_reject_card_{payment_id}")
    kb.button(text="🔙 بازگشت", callback_data="admin_card_transfers")
    kb.button(text="🏠 پنل ادمین", callback_data="admin_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for p in products:
        s = "✅" if p.is_active else "❌"
        kb.button(text=f"{s} {p.name} | {p.price:,.0f}t", callback_data=f"admin_view_prod_{p.id}")
    kb.button(text="➕ افزودن پلن", callback_data="admin_add_product")
    kb.button(text="🔙 بازگشت", callback_data="admin_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_product_edit_kb(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 نام", callback_data=f"edit_prod_name_{product_id}")
    kb.button(text="📊 حجم (GB)", callback_data=f"edit_prod_data_{product_id}")
    kb.button(text="💰 قیمت پایه", callback_data=f"edit_prod_price_{product_id}")
    kb.button(text="📝 توضیحات", callback_data=f"edit_prod_desc_{product_id}")
    kb.button(text="🔄 وضعیت", callback_data=f"admin_toggle_prod_{product_id}")
    kb.button(text="🗑️ حذف", callback_data=f"admin_delete_prod_{product_id}")
    kb.button(text="🔙 بازگشت", callback_data="admin_products")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def admin_user_edit_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚫 مسدود/رفع", callback_data=f"admin_toggle_ban_{user_id}")
    kb.button(text="👑 ادمین", callback_data=f"admin_toggle_admin_{user_id}")
    kb.button(text="💰 شارژ کیف پول", callback_data=f"admin_charge_wallet_{user_id}")
    kb.button(text="🔙 بازگشت", callback_data="admin_users")
    kb.adjust(1)
    return kb.as_markup()


def back_to_admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 بازگشت به پنل ادمین", callback_data="admin_menu")
    return kb.as_markup()


def admin_support_reply_kb(ticket_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f"💬 پاسخ به تیکت #{ticket_id}", callback_data=f"admin_reply_ticket_{ticket_id}")
    kb.button(text="✅ بستن تیکت", callback_data=f"admin_close_ticket_{ticket_id}")
    kb.button(text="🔙 بازگشت", callback_data="admin_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_discounts_kb(codes: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in codes:
        s = "✅" if c.is_active else "❌"
        limit = f"{c.used_count}/{c.max_uses}" if c.max_uses > 0 else f"{c.used_count}/∞"
        kb.button(text=f"{s} {c.code} ({c.percent}% | {limit})", callback_data=f"admin_view_disc_{c.id}")
    kb.button(text="➕ کد جدید", callback_data="admin_add_discount")
    kb.button(text="🔙 بازگشت", callback_data="admin_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_discount_detail_kb(code_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 وضعیت", callback_data=f"admin_toggle_disc_{code_id}")
    kb.button(text="🗑️ حذف", callback_data=f"admin_delete_disc_{code_id}")
    kb.button(text="🔙 بازگشت", callback_data="admin_discounts")
    kb.button(text="🏠 پنل ادمین", callback_data="admin_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_manage_admins_kb() -> InlineKeyboardMarkup:
    """کیبورد مدیریت ادمین‌ها"""
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ افزودن ادمین", callback_data="admin_add_admin")
    kb.button(text="🔙 بازگشت", callback_data="admin_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_remove_admin_kb(admin_ids: list) -> InlineKeyboardMarkup:
    """لیست ادمین‌ها برای حذف"""
    kb = InlineKeyboardBuilder()
    for admin_id in admin_ids:
        kb.button(text=f"❌ حذف {admin_id}", callback_data=f"admin_remove_admin_{admin_id}")
    kb.button(text="🔙 بازگشت", callback_data="admin_manage_admins")
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
    kb.button(text="✏️ تغییر قیمت هر گیگ", callback_data="edit_setting_price_per_gb")
    kb.button(text="✏️ تغییر تخفیف ۷ روزه", callback_data="edit_setting_dur_7")
    kb.button(text="✏️ تغییر تخفیف ۱۰ روزه", callback_data="edit_setting_dur_10")
    kb.button(text="✏️ تغییر تخفیف ۲۰ روزه", callback_data="edit_setting_dur_20")
    # تنظیمات عمومی
    kb.button(text=f"👥 بونس دعوت: {settings.get('referral_bonus', '5000')} تومان", callback_data="noop")
    kb.button(text=f"🧪 روز تست رایگان: {settings.get('free_test_days', '3')}", callback_data="noop")
    kb.button(text="💳 تغییر شماره کارت", callback_data="admin_edit_card")
    kb.button(text="✏️ تغییر بونس دعوت", callback_data="edit_setting_referral_bonus")
    kb.button(text="✏️ تغییر روز تست رایگان", callback_data="edit_setting_free_test_days")
    kb.button(text="🔙 بازگشت", callback_data="admin_menu")
    kb.adjust(1)
    return kb.as_markup()
