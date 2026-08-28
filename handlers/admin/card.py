from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import get_card_info, set_card_info, is_admin
from keyboards.inline import admin_settings_kb, back_to_admin_kb
from states.states import AdminEditCard
from utils.pricing import get_settings

router = Router()


@router.callback_query(F.data == "admin_edit_card")
async def cb_edit_card(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    card_number, card_holder = await get_card_info()
    await callback.message.edit_text(
        "💳 تغییر اطلاعات کارت\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"شماره کارت فعلی: {card_number}\n"
        f"نام صاحب: {card_holder}\n\n"
        "شماره کارت جدید را وارد کنید (۱۶ رقم):",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminEditCard.waiting_number)
    await callback.answer()


@router.message(AdminEditCard.waiting_number)
async def process_card_number(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    card_number = message.text.strip().replace("-", "").replace(" ", "")
    if len(card_number) != 16 or not card_number.isdigit():
        await message.answer("❌ شماره کارت باید ۱۶ رقم باشد:")
        return

    await state.update_data(card_number=card_number)
    await message.answer(
        "✅ شماره کارت ذخیره شد.\n\n"
        "نام صاحب کارت جدید را وارد کنید:"
    )
    await state.set_state(AdminEditCard.waiting_holder)


@router.message(AdminEditCard.waiting_holder)
async def process_card_holder(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    card_holder = message.text.strip()
    if len(card_holder) < 2:
        await message.answer("❌ نام نامعتبر است:")
        return

    data = await state.get_data()
    card_number = data.get("card_number")

    await set_card_info(card_number, card_holder)
    await state.clear()

    await message.answer(
        "✅ اطلاعات کارت به‌روزرسانی شد.\n"
        f"شماره: {card_number}\n"
        f"نام: {card_holder}"
    )

    from utils.pricing import get_settings as _get_settings
    _settings = await _get_settings()
    await message.answer(
        "⚙️ تنظیمات قیمت‌گذاری\n━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=admin_settings_kb(_settings),
    )
