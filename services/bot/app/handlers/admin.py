from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message

from app.storage import fetch_all_user_ids

router = Router()
logger = logging.getLogger(__name__)

ADMIN_TG_ID = 821740830


class BroadcastStates(StatesGroup):
    waiting_for_content = State()


def _is_admin(tg_id: int) -> bool:
    return tg_id == ADMIN_TG_ID


@router.message(Command("broadcast"))
async def broadcast_start(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "📤 Отправьте текст или фото с подписью для рассылки всем пользователям.\n"
        "Для отмены отправьте /cancel"
    )
    await state.set_state(BroadcastStates.waiting_for_content)


@router.message(Command("cancel"), BroadcastStates.waiting_for_content)
async def broadcast_cancel(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("❌ Рассылка отменена.")


@router.message(BroadcastStates.waiting_for_content, F.photo)
async def broadcast_photo(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await state.clear()
        return

    photo = message.photo[-1]
    caption = message.caption or ""
    await state.clear()

    user_ids = fetch_all_user_ids()
    await message.answer(f"📤 Рассылка начата. Получателей: {len(user_ids)}")

    sent = 0
    errors = 0
    for tg_id in user_ids:
        try:
            await message.bot.send_photo(
                tg_id,
                photo.file_id,
                caption=caption,
            )
            sent += 1
        except Exception:
            errors += 1
        await asyncio.sleep(0.05)

    await message.answer(
        f"✅ Рассылка завершена.\nОтправлено: {sent}\nОшибок: {errors}"
    )


@router.message(BroadcastStates.waiting_for_content)
async def broadcast_text(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await state.clear()
        return

    text = message.text
    if not text:
        await message.answer("⚠️ Отправьте текст или фото с подписью.")
        return

    await state.clear()

    user_ids = fetch_all_user_ids()
    await message.answer(f"📤 Рассылка начата. Получателей: {len(user_ids)}")

    sent = 0
    errors = 0
    for tg_id in user_ids:
        try:
            await message.bot.send_message(tg_id, text)
            sent += 1
        except Exception:
            errors += 1
        await asyncio.sleep(0.05)

    await message.answer(
        f"✅ Рассылка завершена.\nОтправлено: {sent}\nОшибок: {errors}"
    )
