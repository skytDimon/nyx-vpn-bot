from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

from app.storage import ensure_user, get_subscription, get_vpn_data

router = Router()


@router.message(Command("subscription"))
@router.message(Command("sub"))
async def subscription_handler(message: Message):
    image_path = Path(__file__).resolve().parents[2] / "img" / "sub.png"
    ensure_user(message.from_user.id, message.from_user.username)
    start_at, end_at = get_subscription(message.from_user.id)
    subscription_link, instructions = get_vpn_data(message.from_user.id)
    if not end_at:
        if image_path.exists():
            await message.answer_photo(
                FSInputFile(str(image_path)),
                caption="❌ Подписка не активна.",
            )
        else:
            await message.answer("❌ Подписка не активна.")
        return
    start_at_str = start_at.isoformat() if start_at else "-"
    end_at_str = end_at.isoformat() if end_at else "-"
    text = f"📌 Статус: active\n🗓️ Начало: {start_at_str}\n📅 Конец: {end_at_str}"
    if instructions:
        text += f"\n\n{instructions}"
    elif subscription_link:
        text += f"\n\n🔗 Ссылка:\n{subscription_link}"
    if image_path.exists():
        await message.answer_photo(FSInputFile(str(image_path)), caption=text)
    else:
        await message.answer(text)
