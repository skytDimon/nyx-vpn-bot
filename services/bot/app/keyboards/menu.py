from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧪 Получить пробник")],
            [KeyboardButton(text="ℹ️ Информация")],
            [KeyboardButton(text="🧑‍💻 Поддержка")],
        ],
        resize_keyboard=True,
    )


def renew_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Продлить", url="https://t.me/nyxsupportvpn")],
        ]
    )
