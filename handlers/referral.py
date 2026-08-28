from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, func

from database.engine import async_session
from database.models import User, ReferralLog
from keyboards.inline import back_to_menu_kb
from locales.fa import TEXTS
from config import get_referral_bonus

router = Router()


@router.callback_query(F.data == "referral")
async def cb_referral(callback: CallbackQuery):
    async with async_session() as session:
        # Count referrals
        count_result = await session.execute(
            select(func.count(ReferralLog.id)).where(
                ReferralLog.referrer_id == callback.from_user.id
            )
        )
        referral_count = count_result.scalar() or 0

        # Total bonus earned
        bonus_result = await session.execute(
            select(func.coalesce(func.sum(ReferralLog.bonus_amount), 0)).where(
                ReferralLog.referrer_id == callback.from_user.id
            )
        )
        total_bonus = bonus_result.scalar() or 0

    bot_username = (await callback.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{callback.from_user.id}"
    bonus = await get_referral_bonus()

    await callback.message.edit_text(
        TEXTS["referral_title"].format(
            bonus=f"{bonus:,}",
            link=referral_link,
            count=referral_count,
            total_bonus=f"{total_bonus:,.0f}",
        ),
        reply_markup=back_to_menu_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()
