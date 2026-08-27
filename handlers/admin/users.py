from decimal import Decimal

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database.engine import async_session
from database.models import User, Payment, PaymentStatus, Ticket, TicketStatus
from keyboards.inline import (
    admin_menu_kb, admin_support_reply_kb, admin_user_edit_kb, back_to_admin_kb,
    admin_card_list_kb, admin_card_detail_kb,
)
from locales.fa import TEXTS
from states.states import AdminChargeWallet
from config import get_admin_ids

router = Router()


@router.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(20)
        )
        users = result.scalars().all()

    lines = ["👥 آخرین کاربران:\n━━━━━━━━━━━━━━━━━━━━━"]
    for user in users:
        status = "🚫" if user.is_banned else "✅"
        admin_badge = " 👑" if user.is_admin else ""
        lines.append(
            f"\n{status}{admin_badge} {user.first_name or 'نامشخص'} "
            f"(@{user.username or 'ندارد'})\n"
            f"💰 {user.wallet_balance:,.0f} تومان | ID: {user.telegram_id}"
        )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    for user in users:
        name = user.first_name or "نامشخص"
        kb.button(text=f"👤 {name}", callback_data=f"admin_view_user_{user.telegram_id}")
    kb.button(text="🔙 بازگشت", callback_data="admin_menu")
    kb.adjust(1)

    await callback.message.edit_text("\n".join(lines), reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_user_"))
async def cb_view_user(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

    if not user:
        await callback.answer("❌ کاربر یافت نشد.", show_alert=True)
        return

    status = "🚫 مسدود" if user.is_banned else "✅ فعال"
    admin = "👑 ادمین" if user.is_admin else "👤 کاربر عادی"
    test = "✅ استفاده شده" if user.used_test else "❌ استفاده نشده"

    text = (
        f"👤 اطلاعات کاربر\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 نام: {user.first_name or 'نامشخص'}\n"
        f"🆔 یوزرنیم: @{user.username or 'ندارد'}\n"
        f"🔢 آیدی: {user.telegram_id}\n"
        f"💰 موجودی: {user.wallet_balance:,.0f} تومان\n"
        f"🔄 وضعیت: {status}\n"
        f"🏷️ نقش: {admin}\n"
        f"🧪 تست: {test}\n"
    )

    await callback.message.edit_text(text, reply_markup=admin_user_edit_kb(user_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_ban_"))
async def cb_toggle_ban(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_banned = not user.is_banned
            await session.commit()

    await callback.answer("✅ وضعیت تغییر کرد.")

    # Refresh view
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

    if user:
        status = "🚫 مسدود" if user.is_banned else "✅ فعال"
        admin = "👑 ادمین" if user.is_admin else "👤 کاربر عادی"
        test = "✅ استفاده شده" if user.used_test else "❌ استفاده نشده"
        text = (
            f"👤 اطلاعات کاربر\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 نام: {user.first_name or 'نامشخص'}\n"
            f"🆔 یوزرنیم: @{user.username or 'ندارد'}\n"
            f"🔢 آیدی: {user.telegram_id}\n"
            f"💰 موجودی: {user.wallet_balance:,.0f} تومان\n"
            f"🔄 وضعیت: {status}\n"
            f"🏷️ نقش: {admin}\n"
            f"🧪 تست: {test}"
        )
        await callback.message.edit_text(text, reply_markup=admin_user_edit_kb(user_id))


@router.callback_query(F.data.startswith("admin_toggle_admin_"))
async def cb_toggle_admin(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_admin = not user.is_admin
            await session.commit()

    await callback.answer("✅ وضعیت ادمین تغییر کرد.")

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

    if user:
        status = "🚫 مسدود" if user.is_banned else "✅ فعال"
        admin = "👑 ادمین" if user.is_admin else "👤 کاربر عادی"
        test = "✅ استفاده شده" if user.used_test else "❌ استفاده نشده"
        text = (
            f"👤 اطلاعات کاربر\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 نام: {user.first_name or 'نامشخص'}\n"
            f"🆔 یوزرنیم: @{user.username or 'ندارد'}\n"
            f"🔢 آیدی: {user.telegram_id}\n"
            f"💰 موجودی: {user.wallet_balance:,.0f} تومان\n"
            f"🔄 وضعیت: {status}\n"
            f"🏷️ نقش: {admin}\n"
            f"🧪 تست: {test}"
        )
        await callback.message.edit_text(text, reply_markup=admin_user_edit_kb(user_id))


@router.callback_query(F.data.startswith("admin_charge_wallet_"))
async def cb_charge_wallet(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    await callback.message.edit_text(
        "💰 مبلغ شارژ (تومان) را وارد کنید:\n\n💡 برای کسر موجودی عدد منفی وارد کنید.",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminChargeWallet.amount)
    await state.update_data(field="wallet", user_id=user_id)
    await callback.answer()


@router.message(AdminChargeWallet.amount)
async def process_admin_charge(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    data = await state.get_data()
    user_id = data["user_id"]

    try:
        amount = Decimal(message.text.replace(",", "").strip())
    except Exception:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید:")
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.wallet_balance += amount
            await session.commit()

    await message.answer(
        f"✅ موجودی کاربر {user_id} تغییر کرد.\n"
        f"💰 مبلغ: {amount:,.0f} تومان\n"
        f"💰 موجودی جدید: {user.wallet_balance:,.0f} تومان",
        reply_markup=admin_menu_kb(),
    )
    await state.clear()


# ===================== Card Transfers =====================

@router.callback_query(F.data == "admin_card_transfers")
async def cb_admin_card_transfers(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(Payment)
            .where(Payment.method == "card_transfer", Payment.status == PaymentStatus.pending)
            .order_by(Payment.created_at.asc())
        )
        payments = result.scalars().all()

        if not payments:
            await callback.message.edit_text(
                "✅ تراکنش کارت به کارت در انتظاری وجود ندارد.",
                reply_markup=admin_menu_kb(),
            )
            await callback.answer()
            return

        # Eagerly load user for each payment
        items = []
        for p in payments:
            user_result = await session.execute(select(User).where(User.telegram_id == p.user_id))
            user = user_result.scalar_one_or_none()
            items.append({"payment": p, "user": user})

    lines = ["⇜ تراکنش‌های کارت به کارت در انتظار:\n━━━━━━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(items, 1):
        pay = item["payment"]
        user = item["user"]
        user_name = (user.first_name or "نامشخص") if user else "نامشخص"
        time_str = pay.created_at.strftime("%H:%M") if pay.created_at else ""
        lines.append(f"\n{i}. 🆔 #{pay.id} | 👤 {user_name} | 💰 {pay.amount:,.0f}t | ⏰ {time_str}")

    kb = admin_card_list_kb(items)
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_card_"))
async def cb_view_card(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    payment_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            await callback.answer("❌ تراکنش یافت نشد.", show_alert=True)
            return

        user_result = await session.execute(select(User).where(User.telegram_id == payment.user_id))
        user = user_result.scalar_one_or_none()

    user_name = (user.first_name or "نامشخص") if user else "نامشخص"
    user_uname = f"@{user.username}" if user and user.username else "ندارد"
    desc = payment.description or "ندارد"

    text = (
        f"⇜ جزئیات تراکنش #{payment.id}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 کاربر: {user_name} ({user_uname})\n"
        f"🆔 آیدی: {payment.user_id}\n\n"
        f"💰 مبلغ: {payment.amount:,.0f} تومان\n"
        f"📝 توضیحات: {desc}\n"
        f"📅 تاریخ: {payment.created_at.strftime('%Y/%m/%d %H:%M') if payment.created_at else 'نامشخص'}"
    )

    await callback.message.edit_text(text, reply_markup=admin_card_detail_kb(payment.id))

    # Send receipt photo if available
    if payment.receipt_file_id:
        try:
            await callback.message.answer_photo(
                photo=payment.receipt_file_id,
                caption=f"📸 رسید پرداخت #{payment.id}\n👤 کاربر: {user_name}\n💰 مبلغ: {payment.amount:,.0f} تومان",
            )
        except Exception:
            await callback.message.answer("📸 رسید پرداخت موجود است (خطا در نمایش)")

    await callback.answer()


@router.callback_query(F.data.startswith("admin_accept_card_"))
async def cb_accept_card(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    payment_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment or payment.status != PaymentStatus.pending:
            await callback.answer("❌ تراکنش یافت نشد یا قبلاً پردازش شده.", show_alert=True)
            return

        payment.status = PaymentStatus.success

        user_result = await session.execute(select(User).where(User.telegram_id == payment.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.wallet_balance += payment.amount
        await session.commit()

    try:
        await callback.bot.send_message(
            payment.user_id,
            TEXTS["card_transfer_approved"].format(amount=f"{payment.amount:,.0f}"),
        )
    except Exception:
        pass

    await callback.answer("✅ تراکنش تایید شد.", show_alert=True)

    # Go back to card transfers list
    await cb_admin_card_transfers(callback)


@router.callback_query(F.data.startswith("admin_reject_card_"))
async def cb_reject_card(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    payment_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if payment and payment.status == PaymentStatus.pending:
            payment.status = PaymentStatus.failed
            await session.commit()

    await callback.answer("❌ تراکنش رد شد.", show_alert=True)

    # Go back to card transfers list
    await cb_admin_card_transfers(callback)


# ===================== Tickets =====================

@router.callback_query(F.data == "admin_tickets")
async def cb_admin_tickets(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(Ticket).where(Ticket.status == TicketStatus.open).order_by(Ticket.created_at.desc())
        )
        tickets = result.scalars().all()

    if not tickets:
        await callback.message.edit_text("✅ تیکت بازی وجود ندارد.", reply_markup=admin_menu_kb())
        await callback.answer()
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    for t in tickets:
        kb.button(text=f"🎫 تیکت #{t.id}", callback_data=f"admin_reply_ticket_{t.id}")
    kb.button(text="🔙 بازگشت", callback_data="admin_menu")
    kb.adjust(1)

    lines = ["🎫 تیکت‌های باز:\n━━━━━━━━━━━━━━━━━━━━━"]
    for t in tickets:
        lines.append(
            f"\n📋 تیکت #{t.id}\n"
            f"👤 کاربر: {t.user_id}\n"
            f"⏰ {t.created_at.strftime('%Y/%m/%d %H:%M') if t.created_at else ''}"
        )

    await callback.message.edit_text("\n".join(lines), reply_markup=kb.as_markup())
    await callback.answer()
