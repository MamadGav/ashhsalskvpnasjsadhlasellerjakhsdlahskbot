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
from utils.texts import EDITABLE_TEXTS, set_custom_text

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

    await state.update_data(text_db_key=db_key, text_key=text_key)
    await callback.message.edit_text(
        f"✏️ ویرایش: {label}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 متن جدید را بفرستید.\n"
        "💡 می‌توانید از ایموجی پرمیوم، بولد، ایتالیک و ... استفاده کنید.\n\n"
        "⚠️ متغیرهای موجود در متن (مثل {name} و {order_id}) را حذف نکنید!\n\n"
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

    # متغیرهای قالب باقی‌مانده را چک کن
    preview = html_text

    await set_custom_text(db_key, html_text)

    await message.answer(
        f"✅ متن «{label}» ذخیره شد!\n\n"
        "━━━ پیش‌نمایش ━━━\n"
        f"{preview}",
        reply_markup=admin_text_confirm_kb(),
        parse_mode="HTML",
    )
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
