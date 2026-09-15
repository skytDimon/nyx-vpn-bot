import asyncio
import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.config import (
    get_admin_id,
    get_payment_amount,
    get_payment_days,
    get_sbp_phone_number,
)
from app.keyboards.menu import main_menu_keyboard
from app.services.xui_client import XuiClient
from app.storage import (
    extend_subscription,
    get_subscription_meta,
    get_user_username,
    record_first_payment_and_reward,
)
from app.utils.email import send_payment_notification

router = Router()
logger = logging.getLogger(__name__)


class PaymentCallback(CallbackData, prefix="payment"):
    action: str
    user_id: int


async def show_sbp_instructions(message: Message):
    """Показать инструкцию по оплате через СБП."""
    amount = get_payment_amount()
    days = get_payment_days()
    phone = get_sbp_phone_number()

    text = (
        f"💳 Продление подписки на {days} дней — {amount}₽\n\n"
        f"1) Переведите {amount}₽ по СБП на номер:\n"
        f"{phone}\n"
        "2) Сфотографируйте или сделайте скриншот чека.\n"
        "3) Пришлите фото чека сюда, в этот чат.\n\n"
        "После проверки администратором подписка продлится автоматически."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(Command("extend"))
@router.message(F.text == "💳 Продлить подписку")
async def extend_handler(message: Message):
    await show_sbp_instructions(message)


@router.message(F.photo)
async def photo_handler(message: Message):
    """Обработка фото чека от пользователя."""
    admin_id = get_admin_id()
    amount = get_payment_amount()

    username = f"@{message.from_user.username}" if message.from_user.username else f"tg_{message.from_user.id}"

    photo = message.photo[-1]
    caption = f"{username} (ID: {message.from_user.id})\nСумма: {amount}₽"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=PaymentCallback(
                        action="approve", user_id=message.from_user.id
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=PaymentCallback(
                        action="reject", user_id=message.from_user.id
                    ).pack(),
                ),
            ]
        ]
    )

    await message.bot.send_photo(
        admin_id,
        photo.file_id,
        caption=caption,
        reply_markup=keyboard,
    )

    await message.answer(
        "📸 Чек отправлен на проверку! Ожидайте подтверждения.",
        reply_markup=main_menu_keyboard(),
    )

    asyncio.create_task(send_payment_notification(username, message.from_user.id))


@router.callback_query(PaymentCallback.filter(F.action == "approve"))
async def approve_payment(callback: CallbackQuery, callback_data: PaymentCallback):
    """Подтвердить оплату."""
    if callback.from_user.id != get_admin_id():
        await callback.answer("❌ Только для администратора", show_alert=True)
        return

    user_id = callback_data.user_id
    days = get_payment_days()

    meta = get_subscription_meta(user_id)
    if not meta:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return

    email = meta.get("client_uuid")
    if not email or not email.startswith("@"):
        username = get_user_username(user_id)
        email = f"@{username}" if username else f"@tg_{user_id}"

    client = XuiClient.from_env()
    try:
        new_end_at = await client.extend_client(
            email, days, current_end_at=meta.get("end_at")
        )
    except Exception:
        logger.exception("Failed to extend XUI client for user %s", user_id)
        await callback.answer("❌ Ошибка продления на панели", show_alert=True)
        return
    finally:
        await client.close()

    extend_subscription(user_id, days)

    reward_result = record_first_payment_and_reward(user_id, reward=75)

    updated_caption = f"{callback.message.caption}\n\n🟢 СТАТУС: ОДОБРЕНО"
    await callback.message.edit_caption(caption=updated_caption, reply_markup=None)

    await callback.bot.send_message(
        user_id,
        f"✅ Оплата подтверждена! Подписка продлена на {days} дней.\n\n"
        f"Новый срок окончания: {new_end_at.strftime('%d.%m.%Y')}",
        reply_markup=main_menu_keyboard(),
    )

    if reward_result:
        referrer_id = reward_result["referrer_tg_id"]
        credited = reward_result["credited"]
        try:
            await callback.bot.send_message(
                referrer_id,
                f"🎁 Ваш друг оплатил подписку! Вам начислено {credited}₽ на реферальный баланс.",
            )
        except Exception:
            logger.exception("Failed to notify referrer %s", referrer_id)

    await callback.answer("✅ Подтверждено")


@router.callback_query(PaymentCallback.filter(F.action == "reject"))
async def reject_payment(callback: CallbackQuery, callback_data: PaymentCallback):
    """Отклонить оплату."""
    if callback.from_user.id != get_admin_id():
        await callback.answer("❌ Только для администратора", show_alert=True)
        return

    user_id = callback_data.user_id

    updated_caption = f"{callback.message.caption}\n\n🔴 СТАТУС: ОТКЛОНЕНО"
    await callback.message.edit_caption(caption=updated_caption, reply_markup=None)

    await callback.bot.send_message(
        user_id,
        "❌ Оплата не найдена. Если вы отправили чек, напишите в поддержку.",
        reply_markup=main_menu_keyboard(),
    )

    await callback.answer("❌ Отклонено")
