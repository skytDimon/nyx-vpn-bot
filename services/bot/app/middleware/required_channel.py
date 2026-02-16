from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.config import get_required_channel_id, get_required_channel_url
from app.keyboards.menu import subscription_check_keyboard


class RequireChannelMiddleware(BaseMiddleware):
    def __init__(self, channel_id: int):
        self._channel_id = channel_id

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        bot = data.get("bot")
        user = data.get("event_from_user")
        if not bot or not user:
            return await handler(event, data)

        try:
            member = await bot.get_chat_member(self._channel_id, user.id)
            if member.status in {"member", "administrator", "creator"}:
                return await handler(event, data)
        except Exception:
            pass

        text = "⚠️ Для использования бота подпишитесь на канал."
        url = get_required_channel_url()
        if url:
            text = f"{text}\n{url}"

        if isinstance(event, CallbackQuery) and event.data == "check:sub":
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            try:
                await event.answer(text, show_alert=True)
            except Exception:
                pass
            try:
                await bot.send_message(
                    user.id, text, reply_markup=subscription_check_keyboard()
                )
            except Exception:
                pass
            return None

        if isinstance(event, Message):
            try:
                await event.answer(text, reply_markup=subscription_check_keyboard())
            except Exception:
                pass
            return None

        try:
            await bot.send_message(
                user.id, text, reply_markup=subscription_check_keyboard()
            )
        except Exception:
            pass
        return None
