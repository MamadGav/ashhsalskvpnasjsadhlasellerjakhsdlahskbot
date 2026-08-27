from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database.engine import async_session
from database.models import User, Ticket, TicketMessage, TicketStatus
from keyboards.inline import back_to_menu_kb, admin_support_reply_kb
from locales.fa import TEXTS
from states.states import SupportState
from config import get_admin_ids

router = Router()


@router.callback_query(F.data == "support")
async def cb_support(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(
            select(Ticket)
            .where(
                Ticket.user_id == callback.from_user.id,
                Ticket.status == TicketStatus.open,
            )
            .order_by(Ticket.created_at.desc())
            .limit(1)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            ticket = Ticket(user_id=callback.from_user.id)
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)

    await callback.message.edit_text(
        TEXTS["support_ticket_open"].format(ticket_id=ticket.id),
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()
    await state.set_state(SupportState.waiting_message)
    await state.update_data(ticket_id=ticket.id)


@router.message(SupportState.waiting_message)
async def process_support_message(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data["ticket_id"]

    async with async_session() as session:
        msg = TicketMessage(
            ticket_id=ticket_id,
            sender_id=message.from_user.id,
            text=message.text or message.caption or "پیام رسانه‌ای",
        )
        session.add(msg)
        await session.commit()

    await message.answer(
        TEXTS["support_ticket_open"].format(ticket_id=ticket_id),
        reply_markup=back_to_menu_kb(),
    )
    await state.clear()

    # Notify all admins
    admin_ids = await get_admin_ids()
    for admin_id in admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                TEXTS["support_admin_notify"].format(
                    ticket_id=ticket_id,
                    user_name=message.from_user.first_name,
                    username=message.from_user.username or "ندارد",
                    user_id=message.from_user.id,
                    message=message.text or "(تصویر/رسانه)",
                ),
                reply_markup=admin_support_reply_kb(ticket_id),
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("admin_reply_ticket_"))
async def cb_admin_reply_ticket(callback: CallbackQuery, state: FSMContext):
    admin_ids = await get_admin_ids()
    if callback.from_user.id not in admin_ids:
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    ticket_id = int(callback.data.split("_")[3])
    await callback.message.edit_text(
        f"💬 پاسخ به تیکت #{ticket_id}\n\n📝 متن پاسخ را ارسال کنید:",
    )
    await state.set_state(SupportState.waiting_message)
    await state.update_data(ticket_id=ticket_id, is_admin_reply=True)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_close_ticket_"))
async def cb_admin_close_ticket(callback: CallbackQuery):
    admin_ids = await get_admin_ids()
    if callback.from_user.id not in admin_ids:
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    ticket_id = int(callback.data.split("_")[3])

    async with async_session() as session:
        result = await session.execute(
            select(Ticket).where(Ticket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        if ticket:
            ticket.status = TicketStatus.closed
            await session.commit()

    await callback.message.edit_text(f"✅ تیکت #{ticket_id} بسته شد.")
    await callback.answer()


@router.callback_query(F.data == "tutorial")
async def cb_tutorial(callback: CallbackQuery):
    await callback.message.edit_text(
        TEXTS["tutorial_title"],
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()
