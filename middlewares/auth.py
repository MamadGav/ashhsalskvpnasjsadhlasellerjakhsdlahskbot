from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from database.engine import async_session
from database.models import User
from utils.texts import t


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id

        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = result.scalar_one_or_none()

        if user and user.is_banned:
            banned_text = (await t("banned"))[:200]
            if isinstance(event, Message):
                await event.answer(banned_text)
            elif isinstance(event, CallbackQuery):
                await event.answer(banned_text, show_alert=True)
            return

        data["db_user"] = user
        return await handler(event, data)
