from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database.engine import async_session
from database.models import DiscountCode
from keyboards.inline import admin_menu_kb, admin_discounts_kb, admin_discount_detail_kb, back_to_admin_kb
from states.states import AdminDiscountCode
from config import get_admin_ids, is_admin

router = Router()


@router.callback_query(F.data == "admin_discounts")
async def cb_admin_discounts(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(DiscountCode).order_by(DiscountCode.created_at.desc())
        )
        codes = result.scalars().all()

    if not codes:
        await callback.message.edit_text(
            "🏷️ هیچ کد تخفیفی وجود ندارد.\n\n💡 روی «افزودن کد جدید» بزنید.",
            reply_markup=admin_discounts_kb([]),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"🏷️ مدیریت کد تخفیف\n━━━━━━━━━━━━━━━━━━━━━\n\n总计: {len(codes)} کد",
        reply_markup=admin_discounts_kb(codes),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_disc_"))
async def cb_view_discount(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    code_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        disc = (await session.execute(
            select(DiscountCode).where(DiscountCode.id == code_id)
        )).scalar_one_or_none()

    if not disc:
        await callback.answer("❌ کد یافت نشد.", show_alert=True)
        return

    status = "✅ فعال" if disc.is_active else "❌ غیرفعال"
    limit = f"{disc.used_count}/{disc.max_uses}" if disc.max_uses > 0 else f"{disc.used_count}/نامحدود"
    expires = disc.expires_at.strftime("%Y/%m/%d %H:%M") if disc.expires_at else "ندارد"

    text = (
        f"🏷️ جزئیات کد تخفیف\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 کد: {disc.code}\n"
        f"📊 درصد: {disc.percent}%\n"
        f"🔄 وضعیت: {status}\n"
        f"🔢 استفاده: {limit}\n"
        f"⏰ انقضا: {expires}\n"
        f"📅 تاریخ ساخت: {disc.created_at.strftime('%Y/%m/%d %H:%M') if disc.created_at else 'نامشخص'}"
    )

    await callback.message.edit_text(text, reply_markup=admin_discount_detail_kb(code_id))
    await callback.answer()


# Add new discount code
@router.callback_query(F.data == "admin_add_discount")
async def cb_add_discount(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    await callback.message.edit_text(
        "🏷️ افزودن کد تخفیف جدید\n\n📝 کد تخفیف را وارد کنید:\n💡 فقط حروف و اعداد (مثال: SUMMER50)",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminDiscountCode.code)
    await callback.answer()


@router.message(AdminDiscountCode.code)
async def process_discount_code(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    code = message.text.strip().upper()

    # Validate
    if len(code) < 3 or len(code) > 32:
        await message.answer("❌ کد باید بین ۳ تا ۳۲ کاراکتر باشد:")
        return

    if not code.isalnum():
        await message.answer("❌ کد فقط باید شامل حروف و اعداد باشد:")
        return

    async with async_session() as session:
        existing = (await session.execute(
            select(DiscountCode).where(DiscountCode.code == code)
        )).scalar_one_or_none()
        if existing:
            await message.answer("❌ این کد قبلاً استفاده شده. کد دیگری وارد کنید:")
            return

    await state.update_data(code=code)
    await message.answer(
        f"✅ کد: {code}\n\n📊 درصد تخفیف را وارد کنید:\n💡 فقط عدد (مثال: 10 به معنی ۱۰٪)",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminDiscountCode.percent)


@router.message(AdminDiscountCode.percent)
async def process_discount_percent(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    try:
        percent = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً یک عدد صحیح وارد کنید:")
        return

    if percent < 1 or percent > 90:
        await message.answer("❌ درصد باید بین ۱ تا ۹۰ باشد:")
        return

    await state.update_data(percent=percent)
    await message.answer(
        f"✅ کد: {await _get_code(state)}\n📊 درصد: {percent}%\n\n🔢 حداکثر دفعات استفاده را وارد کنید:\n💡 0 = نامحدود",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminDiscountCode.max_uses)


async def _get_code(state: FSMContext):
    data = await state.get_data()
    return data.get("code", "?")


@router.message(AdminDiscountCode.max_uses)
async def process_discount_max_uses(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    try:
        max_uses = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً یک عدد صحیح وارد کنید:")
        return

    if max_uses < 0:
        await message.answer("❌ عدد نمی‌تواند منفی باشد:")
        return

    await state.update_data(max_uses=max_uses)
    limit_str = f"{max_uses} بار" if max_uses > 0 else "نامحدود"
    await message.answer(
        f"✅ کد: {await _get_code(state)}\n"
        f"📊 درصد: {await _get_percent(state)}%\n"
        f"🔢 حداکثر: {limit_str}\n\n"
        f"⏰ تاریخ انقضا را وارد کنید:\n"
        f"💡 فرمت: 2026-12-31 یا «ندارد»",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminDiscountCode.expires)


async def _get_percent(state: FSMContext):
    data = await state.get_data()
    return data.get("percent", "?")


@router.message(AdminDiscountCode.expires)
async def process_discount_expires(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    data = await state.get_data()
    expires_at = None
    text = message.text.strip()

    if text != "ندارد":
        try:
            expires_at = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            await message.answer("❌ فرمت تاریخ نادرست است.\n💡 فرمت صحیح: 2026-12-31 یا «ندارد»")
            return

    async with async_session() as session:
        disc = DiscountCode(
            code=data["code"],
            percent=data["percent"],
            max_uses=data.get("max_uses", 0),
            is_active=True,
            expires_at=expires_at,
            created_by=message.from_user.id,
        )
        session.add(disc)
        await session.commit()

    expires_str = expires_at.strftime("%Y/%m/%d") if expires_at else "ندارد"
    limit_str = f"{data.get('max_uses', 0)} بار" if data.get("max_uses", 0) > 0 else "نامحدود"

    await message.answer(
        f"✅ کد تخفیف ساخته شد!\n\n"
        f"🔑 کد: {data['code']}\n"
        f"📊 درصد: {data['percent']}%\n"
        f"🔢 حداکثر: {limit_str}\n"
        f"⏰ انقضا: {expires_str}",
        reply_markup=admin_menu_kb(),
    )
    await state.clear()


# Toggle active
@router.callback_query(F.data.startswith("admin_toggle_disc_"))
async def cb_toggle_discount(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    code_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        disc = (await session.execute(
            select(DiscountCode).where(DiscountCode.id == code_id)
        )).scalar_one_or_none()
        if disc:
            disc.is_active = not disc.is_active
            await session.commit()

    await callback.answer("✅ وضعیت تغییر کرد.")

    # Refresh view
    async with async_session() as session:
        disc = (await session.execute(
            select(DiscountCode).where(DiscountCode.id == code_id)
        )).scalar_one_or_none()

    if disc:
        status = "✅ فعال" if disc.is_active else "❌ غیرفعال"
        limit = f"{disc.used_count}/{disc.max_uses}" if disc.max_uses > 0 else f"{disc.used_count}/∞"
        expires = disc.expires_at.strftime("%Y/%m/%d %H:%M") if disc.expires_at else "ندارد"
        text = (
            f"🏷️ جزئیات کد تخفیف\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 کد: {disc.code}\n"
            f"📊 درصد: {disc.percent}%\n"
            f"🔄 وضعیت: {status}\n"
            f"🔢 استفاده: {limit}\n"
            f"⏰ انقضا: {expires}"
        )
        await callback.message.edit_text(text, reply_markup=admin_discount_detail_kb(code_id))


# Delete
@router.callback_query(F.data.startswith("admin_delete_disc_"))
async def cb_delete_discount(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    code_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        disc = (await session.execute(
            select(DiscountCode).where(DiscountCode.id == code_id)
        )).scalar_one_or_none()
        if disc:
            await session.delete(disc)
            await session.commit()

    await callback.answer("🗑️ کد تخفیف حذف شد.", show_alert=True)

    # Go back to list
    async with async_session() as session:
        codes = (await session.execute(
            select(DiscountCode).order_by(DiscountCode.created_at.desc())
        )).scalars().all()

    if codes:
        await callback.message.edit_text(
            f"🏷️ مدیریت کد تخفیف\n━━━━━━━━━━━━━━━━━━━━━\n总计: {len(codes)} کد",
            reply_markup=admin_discounts_kb(codes),
        )
    else:
        await callback.message.edit_text(
            "🏷️ هیچ کد تخفیفی وجود ندارد.",
            reply_markup=admin_discounts_kb([]),
        )
