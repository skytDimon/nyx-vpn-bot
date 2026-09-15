import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards.menu import main_menu_keyboard
from app.storage import get_referral_info

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("ref"))
@router.message(lambda message: message.text in {"👥 Пригласить друга", "Пригласить друга"})
async def referral_handler(message: Message):
    tg_id = message.from_user.id

    try:
        bot_username = (await message.bot.get_me()).username
    except Exception:
        bot_username = "nyxvpn_bot"

    ref_link = f"https://t.me/{bot_username}?start=ref_{tg_id}"

    try:
        info = get_referral_info(tg_id)
    except Exception:
        logger.exception("Failed to get referral info for %s", tg_id)
        info = {"referral_balance": 0, "invited_count": 0}

    text = (
        f"👥 Пригласи друга и получи 75₽ за каждого!\n\n"
        f"🔗 Твоя ссылка:\n"
        f"`{ref_link}`\n\n"
        f"📊 Статистика:\n"
        f"• Приглашено: {info['invited_count']} чел.\n"
        f"• На балансе: {info['referral_balance']}₽\n\n"
        f"📝 Правила:\n"
        f"• Друг должен перейти по твоей ссылке и оплатить подписку.\n"
        f"• Бонус начисляется только за первую оплату друга.\n"
        f"• 75₽ за каждого приглашённого, кто оплатил!\n"
        f"• Копишь до 150₽ — получаешь 1 месяц бесплатно."
    )

    await message.answer(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )
