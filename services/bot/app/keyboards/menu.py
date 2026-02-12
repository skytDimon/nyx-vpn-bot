from urllib.parse import quote

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💼 Тарифы"),
                KeyboardButton(text="👤 Личный кабинет"),
            ],
            [KeyboardButton(text="ℹ️ Информация")],
            [KeyboardButton(text="⚙️ Настройка")],
            [KeyboardButton(text="🎁 Пригласи друга")],
            [KeyboardButton(text="🧑‍💻 Help")],
        ],
        resize_keyboard=True,
    )


def tariffs_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Подключить", callback_data="tariff:connect"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧪 Пробный доступ", callback_data="tariff:trial"
                )
            ],
        ]
    )


def payments_keyboard() -> InlineKeyboardMarkup:
    support_text = "привет хочу купить подписку на впн"
    support_url = f"https://t.me/SkytNinja?text={quote(support_text)}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить с баланса", callback_data="pay:balance"
                )
            ],
            [InlineKeyboardButton(text="🏦 Оплатить через РФ банк", url=support_url)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:countries")],
        ]
    )


def balance_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:cabinet")],
        ]
    )


def balance_payments_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:balance")],
        ]
    )


def personal_cabinet_keyboard(show_buy: bool = False) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="💰 Баланс", callback_data="balance:open")]]
    if show_buy:
        buttons.insert(
            0, [InlineKeyboardButton(text="🛒 Купить", callback_data="cabinet:buy")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def setup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="V2rayTun", callback_data="setup:v2raytun")],
            [InlineKeyboardButton(text="Happ", callback_data="setup:happ")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:setup")],
        ]
    )


def countries_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇫🇮 Finland", callback_data="country:fi")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:tariffs")],
        ]
    )


def plans_keyboard(plans: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=plan["name"], callback_data=f"plan:{plan['id']}")]
        for plan in plans
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_keyboard(plan_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оплатить с баланса",
                    callback_data=f"pay:balance:{plan_id}",
                )
            ],
        ]
    )
