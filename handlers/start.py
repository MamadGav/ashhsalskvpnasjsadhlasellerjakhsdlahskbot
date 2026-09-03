from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from database.engine import async_session
from database.models import User, ReferralLog
from keyboards.inline import main_menu_kb
from config import BOT_TOKEN, get_referral_bonus, get_admin_ids
from utils.icons import tg
from utils.texts import t, esc

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    args = message.text.split(maxsplit=1)
    referrer_id = None

    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].split("ref_")[1])
        except (ValueError, IndexError):
            referrer_id = None

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                referred_by_id=referrer_id,
            )
            session.add(user)
            await session.commit()

            # Give referral bonus
            if referrer_id and referrer_id != message.from_user.id:
                ref_result = await session.execute(
                    select(User).where(User.telegram_id == referrer_id)
                )
                referrer = ref_result.scalar_one_or_none()
                if referrer:
                    bonus = Decimal(str(await get_referral_bonus()))
                    referrer.wallet_balance += bonus
                    user.wallet_balance += bonus

                    log = ReferralLog(
                        referrer_id=referrer_id,
                        referred_id=message.from_user.id,
                        bonus_amount=bonus,
                    )
                    session.add(log)
                    await session.commit()

                    await message.answer(
                        (await t("welcome_referral")).format(
                            name=esc(user.first_name or "کاربر"),
                            referrer=esc(referrer.first_name or "کاربر"),
                            bonus=f"{bonus:,.0f}",
                        ),
                        reply_markup=main_menu_kb(),
                    )
                    return

        else:
            user.username = message.from_user.username
            user.first_name = message.from_user.first_name
            await session.commit()

    await message.answer(
        (await t("welcome")).format(
            name=esc(message.from_user.first_name or "کاربر"),
            gem=tg("gem"), lock=tg("lock"), bolt=tg("bolt"),
        ),
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "menu")
async def cb_menu(callback, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        await t("menu"),
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
