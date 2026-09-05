"""
📝 پنل ویرایش متن‌های ربات توسط ادمین
ادمین متن جدید را با ایموجی پرمیوم می‌فرستد؛
entities پیام به HTML تبدیل و ذخیره می‌شود.
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.text_decorations import html_decoration

from keyboards.inline import (
    admin_menu_kb, back_to_admin_kb, admin_texts_kb, admin_text_confirm_kb,
    admin_text_confirm_kb_custom,
)
from locales.fa import TEXTS
from states.states import AdminEditText
from config import is_admin
from utils.texts import (
    EDITABLE_TEXTS, TEXT_VARIABLES, set_custom_text,
    visible_len, MAX_VISIBLE_LEN, split_html_message,
)

router = Router()


@router.callback_query(F.data == "admin_texts")
async def cb_admin_texts(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    await callback.message.edit_text(
        "📝 ویرایش متن‌های ربات\n━━━━━━━━━━━━━━━━━━━━━\n"
        "روی متن مورد نظر کلیک کنید تا ویرایشش کنید.\n\n"
        "💡 می‌توانید متن را با ایموجی پرمیوم بفرستید — "
        "به همان شکل برای کاربران نمایش داده می‌شود.",
        reply_markup=admin_texts_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_text_"))
async def cb_edit_text(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    db_key = callback.data.replace("admin_edit_text_", "")
    info = EDITABLE_TEXTS.get(db_key)
    if not info:
        await callback.answer("❌", show_alert=True)
        return

    text_key, label = info

    # راهنمای متغیرهای این متن
    variables = TEXT_VARIABLES.get(db_key, ())
    if variables:
        vars_help = " | ".join(f"{{{v}}}" for v in variables)
        vars_block = f"\n\n🧩 متغیرهای این متن (حذفشان نکنید):\n<code>{vars_help}</code>"
    else:
        vars_block = "\n\n🧩 این متن متغیری ندارد — کاملاً آزاد است."

    await state.update_data(text_db_key=db_key, text_key=text_key)
    await callback.message.edit_text(
        f"✏️ ویرایش: {label}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 متن جدید را بفرستید.\n"
        "💡 می‌توانید از ایموجی پرمیوم، بولد، ایتالیک و ... استفاده کنید."
        f"{vars_block}\n\n"
        f"📏 حداکثر طول متن: ~{MAX_VISIBLE_LEN} کاراکتر.\n\n"
        "♻️ برای بازگشت به متن پیش‌فرض، فقط «reset» بفرستید.",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminEditText.value)
    await callback.answer()


@router.message(AdminEditText.value)
async def process_edit_text(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    data = await state.get_data()
    db_key = data["text_db_key"]
    text_key = data["text_key"]
    label = EDITABLE_TEXTS[db_key][1]

    # reset → بازگشت به متن پیش‌فرض (مقدار خالی در دیتابیس = پیش‌فرض)
    if message.text and message.text.strip().lower() == "reset":
        await set_custom_text(db_key, "")

        await message.answer(
            f"♻️ متن «{label}» به پیش‌فرض بازگشت.",
            reply_markup=admin_menu_kb(),
        )
        await state.clear()
        return

    # تبدیل entities پیام ادمین به HTML (شامل tg-emoji پرمیوم)
    html_text = html_decoration.unparse(message.text or "", message.entities or [])

    # اعتبارسنجی طول مرئی (تلگرام تگ‌ها را نمی‌شمارد؛ هر ایموجی پرمیوم = ۲ واحد)
    vlen = visible_len(html_text)
    if vlen > MAX_VISIBLE_LEN:
        await message.answer(
            f"❌ متن خیلی بلند است! ({vlen} کاراکتر)\n"
            f"📏 حداکثر مجاز: {MAX_VISIBLE_LEN} کاراکتر.\n\n"
            "💡 متن را کوتاه‌تر کنید یا به چند بخش تقسیمش کنید.",
        )
        return  # state حفظ می‌شود تا ادمین دوباره بفرستد

    preview = html_text

    await set_custom_text(db_key, html_text)

    # پیش‌نمایش: اگر بلند بود به چند پیام تقسیم می‌شود
    for i, chunk in enumerate(split_html_message(f"✅ متن «{label}» ذخیره شد!\n\n━━━ پیش‌نمایش ━━━\n{preview}")):
        kb = admin_text_confirm_kb() if i == 0 else None
        await message.answer(chunk, reply_markup=kb, parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data.startswith("admin_preview_text_"))
async def cb_preview_text(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    db_key = callback.data.replace("admin_preview_text_", "")
    info = EDITABLE_TEXTS.get(db_key)
    if not info:
        await callback.answer("❌", show_alert=True)
        return

    text_key, label = info
    from utils.texts import get_custom_text
    custom = await get_custom_text(db_key)

    if custom:
        await callback.message.edit_text(
            f"👀 متن فعلی «{label}» (سفارشی):\n━━━━━━━━━━━━━━━━━━━━━\n\n{custom}",
            reply_markup=admin_text_confirm_kb_custom(db_key),
            parse_mode="HTML",
        )
    else:
        default = TEXTS.get(text_key, "")
        await callback.message.edit_text(
            f"👀 متن فعلی «{label}» (پیش‌فرض):\n━━━━━━━━━━━━━━━━━━━━━\n\n{default}",
            reply_markup=admin_text_confirm_kb_custom(db_key),
            parse_mode="HTML",
        )
    await callback.answer()
