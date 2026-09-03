from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import get_admin_ids, add_admin, remove_admin, is_admin
from keyboards.inline import (
    admin_menu_kb, admin_manage_admins_kb, admin_remove_admin_kb, back_to_admin_kb,
)
from states.states import AdminManageAdmin

router = Router()


def _admins_text(admin_ids: list) -> str:
    return (
        "👑 مدیریت ادمین‌ها\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"تعداد ادمین‌ها: {len(admin_ids)}\n"
        f"لیست: {', '.join(str(x) for x in admin_ids)}"
    )


@router.callback_query(F.data == "admin_manage_admins")
async def cb_manage_admins(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    admin_ids = await get_admin_ids()
    await callback.message.edit_text(
        _admins_text(admin_ids),
        reply_markup=admin_manage_admins_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_admin")
async def cb_add_admin(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    await callback.message.edit_text(
        "➕ افزودن ادمین جدید\n━━━━━━━━━━━━━━━━━━━━━\n"
        "آیدی عددی کاربر را وارد کنید:\n"
        "(از @userinfobot قابل دریافت است)",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminManageAdmin.waiting_user_id)
    await callback.answer()


@router.message(AdminManageAdmin.waiting_user_id)
async def process_add_admin(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً عدد صحیح وارد کنید:")
        return

    if user_id <= 0:
        await message.answer("❌ آیدی نامعتبر است:")
        return

    success = await add_admin(user_id)
    if success:
        await message.answer(f"✅ کاربر {user_id} به لیست ادمین‌ها اضافه شد.")
    else:
        await message.answer(f"⚠️ کاربر {user_id} از قبل ادمین است.")

    await state.clear()
    admin_ids = await get_admin_ids()
    await message.answer(
        _admins_text(admin_ids),
        reply_markup=admin_manage_admins_kb(),
    )


@router.callback_query(F.data == "admin_remove_admin_menu")
async def cb_remove_admin_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    admin_ids = await get_admin_ids()

    if len(admin_ids) <= 1:
        await callback.answer(
            "⚠️ حداقل یک ادمین باید باقی بماند!",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "➖ حذف ادمین\n━━━━━━━━━━━━━━━━━━━━━\n"
        "روی ادمین مورد نظر کلیک کنید:",
        reply_markup=admin_remove_admin_kb(admin_ids),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_remove_admin_"))
async def cb_remove_admin(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    # جلوگیری از حذف آخرین ادمین
    admin_ids = await get_admin_ids()
    if len(admin_ids) <= 1:
        await callback.answer(
            "⚠️ حداقل یک ادمین باید باقی بماند!",
            show_alert=True,
        )
        return

    # جلوگیری از حذف خود
    if user_id == callback.from_user.id:
        await callback.answer("⚠️ نمی‌توانید خودتان را حذف کنید!", show_alert=True)
        return

    success = await remove_admin(user_id)

    if success:
        await callback.answer(f"✅ ادمین {user_id} حذف شد", show_alert=True)
    else:
        await callback.answer("❌ ادمین یافت نشد", show_alert=True)

    admin_ids = await get_admin_ids()
    await callback.message.edit_text(
        _admins_text(admin_ids),
        reply_markup=admin_manage_admins_kb(),
    )
