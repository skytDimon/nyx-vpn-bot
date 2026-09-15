import logging
from datetime import datetime, timedelta, timezone

import jwt
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import get_cabinet_url, get_jwt_secret
from app.keyboards.menu import main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("cabinet"))
@router.message(lambda message: message.text in {"👤 Личный кабинет", "Личный кабинет"})
async def cabinet_handler(message: Message):
    tg_id = message.from_user.id
    secret = get_jwt_secret()
    cabinet_url = get_cabinet_url()

    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    token = jwt.encode({"sub": tg_id, "exp": int(exp.timestamp())}, secret, algorithm="HS256")

    url = f"{cabinet_url}/cabinet?t={token}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть личный кабинет", url=url)]
        ]
    )

    text = (
        "👤 Личный кабинет\n\n"
        "Нажмите кнопку ниже, чтобы открыть веб-кабинет.\n"
        "Ссылка действительна 1 час."
    )

    await message.answer(text, reply_markup=keyboard)
