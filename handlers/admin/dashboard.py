from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, func

from database.engine import async_session
from database.models import User, Order, Payment, Ticket, TicketStatus
from keyboards.inline import admin_menu_kb
from locales.fa import TEXTS
from config import get_admin_ids, is_admin
from utils.texts import esc
from aiogram.fsm.context import FSMContext

router = Router()


@router.callback_query(F.data == "admin_menu")
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    await state.clear()

    async with async_session() as session:
        users_count = (await session.execute(select(func.count(User.id)))).scalar() or 0
        orders_count = (await session.execute(select(func.count(Order.id)))).scalar() or 0
        payments_count = (await session.execute(select(func.count(Payment.id)))).scalar() or 0
        open_tickets = (await session.execute(
            select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.open)
        )).scalar() or 0

    await callback.message.edit_text(
        TEXTS["admin_dashboard"].format(
            users=users_count,
            orders=orders_count,
            payments=payments_count,
            tickets=open_tickets,
        ),
        reply_markup=admin_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_dashboard")
async def cb_admin_dashboard(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    await cb_admin_menu(callback)


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی ادمین ندارید.")
        return

    await message.answer(
        "📊 پنل ادمین",
        reply_markup=admin_menu_kb(),
    )
