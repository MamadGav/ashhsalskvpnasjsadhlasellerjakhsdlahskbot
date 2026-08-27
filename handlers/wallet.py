from decimal import Decimal, InvalidOperation

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database.engine import async_session
from database.models import User, Payment, PaymentStatus
from keyboards.inline import wallet_methods_kb, back_to_menu_kb
from locales.fa import TEXTS
from states.states import WalletCharge
from config import get_admin_ids, get_card_info

router = Router()


@router.callback_query(F.data == "wallet")
async def cb_wallet(callback: CallbackQuery):
    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )).scalar_one_or_none()

    balance = f"{user.wallet_balance:,.0f}" if user else "0"
    await callback.message.edit_text(
        TEXTS["wallet_title"].format(balance=balance),
        reply_markup=wallet_methods_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "wallet_card")
async def cb_wallet_card(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        TEXTS["wallet_enter_amount"],
        reply_markup=back_to_menu_kb(),
    )
    await state.set_state(WalletCharge.enter_amount)
    await callback.answer()


@router.message(WalletCharge.enter_amount)
async def process_enter_amount(message: Message, state: FSMContext):
    try:
        amount = Decimal(message.text.replace(",", "").replace(".", "").strip())
    except (InvalidOperation, ValueError, AttributeError):
        await message.answer(TEXTS["wallet_invalid_amount"])
        return

    if amount < Decimal("10000"):
        await message.answer(TEXTS["wallet_amount_too_low"])
        return

    card_number, card_holder = await get_card_info()

    await message.answer(
        TEXTS["wallet_card_info"].format(
            card_number=card_number,
            card_holder=card_holder,
            amount=f"{amount:,.0f}",
        ),
        reply_markup=back_to_menu_kb(),
        parse_mode="Markdown",
    )
    await state.update_data(amount=str(amount))
    await state.set_state(WalletCharge.upload_receipt)


@router.message(WalletCharge.upload_receipt, F.photo)
async def process_upload_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = Decimal(data["amount"])
    receipt_file_id = message.photo[-1].file_id

    async with async_session() as session:
        payment = Payment(
            user_id=message.from_user.id,
            amount=amount,
            method="card_transfer",
            status=PaymentStatus.pending,
            description=f"کارت به کارت - رسید از {message.from_user.first_name}",
            receipt_file_id=receipt_file_id,
        )
        session.add(payment)
        await session.commit()

    await message.answer(TEXTS["wallet_receipt_received"], reply_markup=back_to_menu_kb())
    await state.clear()

    admin_ids = await get_admin_ids()
    for admin_id in admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                TEXTS["admin_new_receipt"].format(
                    user_name=message.from_user.first_name,
                    user_id=message.from_user.id,
                    amount=f"{amount:,.0f}",
                ),
            )
            await message.bot.send_photo(
                admin_id,
                photo=receipt_file_id,
                caption=f"📸 رسید پرداخت\n👤 {message.from_user.first_name} (ID: {message.from_user.id})\n💰 {amount:,.0f} تومان",
            )
        except Exception:
            pass


@router.message(WalletCharge.upload_receipt)
async def process_invalid_receipt(message: Message):
    await message.answer("❌ لطفاً تصویر رسید را ارسال کنید.")
