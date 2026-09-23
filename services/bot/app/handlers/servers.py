"""Handler for the 📡 Серверы button — shows VPN server status."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.keyboards.menu import main_menu_keyboard
from app.services.server_monitor import (
    can_refresh,
    check_all_servers,
    get_cached_status,
)

router = Router()
logger = logging.getLogger(__name__)


def _format_status(statuses: list[dict]) -> str:
    """Build a user-facing status message (no IPs exposed)."""
    lines = ["📡 <b>Состояние серверов</b>\n"]
    for s in statuses:
        icon = "🟢" if s["alive"] else "🔴"
        latency = f" — {int(s['latency_ms'])} мс" if s.get("latency_ms") else ""
        status_text = "онлайн" if s["alive"] else "офлайн"
        lines.append(f"{icon} {s['name']}{latency} ({status_text})")

    # Show last check time
    if statuses and statuses[0].get("checked_at"):
        try:
            checked = datetime.fromisoformat(statuses[0]["checked_at"])
            # Convert to Moscow time (UTC+3) for display
            from datetime import timedelta

            msk = checked + timedelta(hours=3)
            lines.append(f"\n🕐 Обновлено: {msk.strftime('%d.%m.%Y в %H:%M')} МСК")
        except (ValueError, TypeError):
            pass

    return "\n".join(lines)


def _refresh_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="servers:refresh")],
        ]
    )


@router.message(Command("servers"))
@router.message(lambda message: message.text in {"📡 Серверы", "Серверы"})
async def servers_handler(message: Message):
    statuses = get_cached_status()
    if statuses is None:
        await message.answer(
            "⏳ Проверяю серверы...",
            reply_markup=main_menu_keyboard(),
        )
        statuses = await check_all_servers()

    if not statuses:
        await message.answer(
            "⚠️ Серверы не настроены.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        _format_status(statuses),
        reply_markup=_refresh_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "servers:refresh")
async def servers_refresh_callback(callback: CallbackQuery):
    if not can_refresh():
        await callback.answer("⏳ Подождите минуту перед повторным обновлением", show_alert=False)
        return

    await callback.answer("🔄 Обновляю...")
    statuses = await check_all_servers()

    if not statuses:
        await callback.message.edit_text(
            "⚠️ Серверы не настроены.",
        )
        return

    await callback.message.edit_text(
        _format_status(statuses),
        reply_markup=_refresh_keyboard(),
        parse_mode="HTML",
    )
