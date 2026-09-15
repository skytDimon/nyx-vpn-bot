from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.config import get_trial_days
from app.keyboards.menu import main_menu_keyboard, renew_keyboard
from app.services.xui_client import XuiClient
from app.storage import (
    claim_pending_for_user,
    ensure_user,
    get_subscription,
    is_trial_used,
    set_subscription,
    set_trial_used,
)
from app.vpn_instructions import APPSTORE_SECTION, WHITELIST_SECTION, vpn_instructions

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_handler(message: Message):
    ensure_user(message.from_user.id, message.from_user.username)
    claim = claim_pending_for_user(message.from_user.id, message.from_user.username)
    if claim:
        logger.info(
            "claimed pending subscription for tg_id=%s username=%s end_at=%s",
            message.from_user.id,
            message.from_user.username,
            claim.get("end_at"),
        )

    payload = _extract_start_payload(message.text)
    if payload:
        if payload.startswith("ref_"):
            try:
                referrer_tg_id = int(payload[4:])
                from app.storage import set_referrer
                if set_referrer(message.from_user.id, referrer_tg_id):
                    logger.info("Set referrer %s for user %s", referrer_tg_id, message.from_user.id)
            except (ValueError, IndexError):
                pass
        elif payload == "extend":
            from app.handlers.payment import show_sbp_instructions
            await show_sbp_instructions(message)
            return

    image_path = Path(__file__).resolve().parents[2] / "img" / "start.png"
    if claim:
        end_at = claim.get("end_at")
        end_s = end_at.strftime("%d.%m.%Y") if end_at else "—"
        text = (
            "🐾 Привет! Это твой личный VPN‑сервис.\n"
            "🌐 Свободный интернет прямо в Telegram.\n\n"
            f"✅ Мы нашли твою активную подписку в системе — она доступна до {end_s}.\n"
            "Открой «Личный кабинет», чтобы получить ссылку."
        )
    else:
        text = (
            "🐾 Привет! Это твой личный VPN‑сервис.\n"
            "🌐 Свободный интернет прямо в Telegram.\n\n"
            "Нажми кнопку ниже, чтобы получить пробный доступ на 3 дня."
        )
    if image_path.exists():
        await message.answer_photo(
            FSInputFile(str(image_path)),
            caption=text,
            reply_markup=main_menu_keyboard(),
        )
    else:
        await message.answer(text, reply_markup=main_menu_keyboard())


def _extract_start_payload(text: str | None) -> str | None:
    """Извлечь payload из /start команды."""
    if not text:
        return None
    parts = text.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else None


@router.message(Command("help"))
@router.message(lambda message: message.text in {"Поддержка", "🧑‍💻 Поддержка"})
async def help_handler(message: Message):
    await message.answer(
        "🧑‍💻 Саппорт: @nyxsupportvpn\nВремя ответа ~2 часа",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("info"))
@router.message(lambda message: message.text in {"ℹ️ Информация", "Информация"})
async def info_handler(message: Message):
    image_path = Path(__file__).resolve().parents[2] / "img" / "info.png"
    text = (
        "ℹ️ Информация\n\n"
        "VPN-сервис с пробным периодом 3 дня.\n"
        "Для продления обратитесь в поддержку.\n\n"
        "🔗 Серверы подключаются автоматически через подписку.\n"
        "📱 Поддерживаемые клиенты: v2rayN, Streisand, V2Ray Tun.\n"
        "🔒 Безопасность: мы не собираем данные о трафике.\n\n"
        "💬 Вопросы — пишите в поддержку."
    )
    if image_path.exists():
        await message.answer_photo(
            FSInputFile(str(image_path)),
            caption=text,
            reply_markup=main_menu_keyboard(),
        )
    else:
        await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(Command("appstore"))
@router.message(lambda message: message.text in {"🍎 App Store", "App Store"})
async def appstore_handler(message: Message):
    await message.answer(APPSTORE_SECTION, reply_markup=main_menu_keyboard())


@router.message(Command("whitelist"))
@router.message(lambda message: message.text in {"🌐 Белый список", "Белый список"})
async def whitelist_handler(message: Message):
    await message.answer(WHITELIST_SECTION, reply_markup=main_menu_keyboard())


@router.message(lambda message: message.text in {"🧪 Получить пробник", "Получить пробник"})
async def trial_button_handler(message: Message):
    await _request_trial(message.from_user, message)


@router.callback_query(F.data == "trial:request")
async def trial_callback(callback: CallbackQuery):
    await _request_trial(callback.from_user, callback.message, callback)
    await callback.answer()


async def _request_trial(user, message, callback=None):
    ensure_user(user.id, user.username)
    claim_pending_for_user(user.id, user.username)

    if is_trial_used(user.id):
        _, end_at = get_subscription(user.id)
        end_at = _normalize_dt(end_at)
        if end_at and end_at >= datetime.now(timezone.utc):
            meta = _get_subscription_link(user.id)
            sub_link = meta.get("subscription_link") if meta else None
            if sub_link:
                instructions = vpn_instructions(sub_link)
                text = (
                    f"✅ У вас уже есть активный пробник до {end_at.strftime('%d.%m.%Y')}.\n\n"
                    f"{instructions}"
                )
            else:
                text = f"✅ У вас уже есть активный пробник до {end_at.strftime('%d.%m.%Y')}."
            await message.answer(text, reply_markup=main_menu_keyboard(), disable_web_page_preview=True)
        else:
            await message.answer(
                "❌ Вы уже использовали пробный период.\n"
                "Для продления обратитесь в поддержку:",
                reply_markup=renew_keyboard(),
            )
        return

    _, end_at = get_subscription(user.id)
    end_at = _normalize_dt(end_at)
    if end_at and end_at >= datetime.now(timezone.utc):
        meta = _get_subscription_link(user.id)
        sub_link = meta.get("subscription_link") if meta else None
        if sub_link:
            instructions = vpn_instructions(sub_link)
            text = (
                f"✅ У вас уже есть активный пробник до {end_at.strftime('%d.%m.%Y')}.\n\n"
                f"{instructions}"
            )
        else:
            text = f"✅ У вас уже есть активный пробник до {end_at.strftime('%d.%m.%Y')}."
        await message.answer(text, reply_markup=main_menu_keyboard(), disable_web_page_preview=True)
        return

    username = f"@{user.username}" if user.username else f"@tg_{user.id}"
    trial_days = get_trial_days()

    client = XuiClient.from_env()
    try:
        sub_id = await client.add_client(email=username, days=trial_days)
    except httpx.TimeoutException:
        await message.answer(
            "⚠️ Сервис временно недоступен. Попробуйте чуть позже.",
            reply_markup=main_menu_keyboard(),
        )
        return
    except httpx.HTTPStatusError as e:
        logger.error("XUI API error: %s", e)
        await message.answer(
            "⚠️ Ошибка при создании пробника. Попробуйте чуть позже.",
            reply_markup=main_menu_keyboard(),
        )
        return
    except Exception:
        logger.exception("Unexpected error creating trial for tg_id=%s", user.id)
        await message.answer(
            "⚠️ Произошла ошибка. Попробуйте чуть позже.",
            reply_markup=main_menu_keyboard(),
        )
        return
    finally:
        await client.close()

    sub_link = client.subscription_link(sub_id)
    instructions = vpn_instructions(sub_link)

    start_at = datetime.now(timezone.utc)
    end_at = start_at + timedelta(days=trial_days)
    set_subscription(
        user.id,
        start_at,
        end_at,
        sub_link,
        instructions,
        "nl",
        client_uuid=username,
        sub_id=sub_id,
    )
    set_trial_used(user.id)

    link_image = Path(__file__).resolve().parents[2] / "img" / "link.png"
    try:
        if link_image.exists():
            await message.bot.send_photo(
                user.id,
                FSInputFile(str(link_image)),
                caption=instructions,
                reply_markup=main_menu_keyboard(),
            )
        else:
            await message.bot.send_message(
                user.id,
                instructions,
                reply_markup=main_menu_keyboard(),
                disable_web_page_preview=True,
            )
    except Exception:
        logger.exception("Trial send failed for tg_id=%s", user.id)


def _get_subscription_link(tg_id: int) -> dict | None:
    from app.storage import get_subscription_meta
    return get_subscription_meta(tg_id)


def _normalize_dt(value: datetime | None) -> datetime | None:
    if not value:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
