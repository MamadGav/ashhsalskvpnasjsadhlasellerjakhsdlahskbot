from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database.engine import async_session
from database.models import BotSettings
from keyboards.inline import admin_menu_kb, admin_settings_kb, back_to_admin_kb
from states.states import AdminEditSetting
from config import get_admin_ids, is_admin

router = Router()


async def _get_settings() -> dict:
    async with async_session() as session:
        result = await session.execute(select(BotSettings))
        return {s.key: s.value for s in result.scalars().all()}


@router.callback_query(F.data == "admin_settings")
async def cb_admin_settings(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    settings = await _get_settings()
    await callback.message.edit_text(
        "⚙️ تنظیمات قیمت‌گذاری\n━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=admin_settings_kb(settings),
    )
    await callback.answer()


_SETTING_LABELS = {
    "edit_setting_price_per_gb": ("price_per_gb", "قیمت هر گیگ (تومان)"),
    "edit_setting_dur_7": ("dur_7_discount", "تخفیف ۷ روزه (تومان از قیمت پایه)"),
    "edit_setting_dur_10": ("dur_10_discount", "تخفیف ۱۰ روزه (تومان)"),
    "edit_setting_dur_20": ("dur_20_discount", "تخفیف ۲۰ روزه (تومان)"),
    "edit_setting_referral_bonus": ("referral_bonus", "بونس دعوت از دوستان (تومان)"),
    "edit_setting_free_test_days": ("free_test_days", "روزهای تست رایگان"),
}


@router.callback_query(F.data.startswith("edit_setting_"))
async def cb_edit_setting(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    key, label = _SETTING_LABELS.get(callback.data, (None, None))
    if not key:
        await callback.answer("❌", show_alert=True)
        return

    settings = await _get_settings()
    current = settings.get(key, "?")

    await state.update_data(setting_key=key)
    await callback.message.edit_text(
        f"✏️ {label}\n\nمقدار فعلی: {current}\n\nمقدار جدید را وارد کنید:",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminEditSetting.value)
    await callback.answer()


@router.message(AdminEditSetting.value)
async def process_edit_setting(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    data = await state.get_data()
    key = data.get("setting_key")
    if not key:
        await message.answer("❌ خطا", reply_markup=admin_menu_kb())
        await state.clear()
        return

    try:
        val = int(message.text.replace(",", "").strip())
    except ValueError:
        await message.answer("❌ لطفاً عدد صحیح وارد کنید:")
        return

    if val < 0:
        await message.answer("❌ عدد نمی‌تواند منفی باشد:")
        return

    async with async_session() as session:
        setting = (await session.execute(
            select(BotSettings).where(BotSettings.key == key)
        )).scalar_one_or_none()

        if setting:
            setting.value = str(val)
        else:
            session.add(BotSettings(key=key, value=str(val)))

        await session.commit()

    await message.answer("✅ تنظیمات به‌روزرسانی شد.", reply_markup=admin_menu_kb())
    await state.clear()
