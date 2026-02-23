import logging
import logging
from pathlib import Path

from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.keyboards.menu import (
    balance_keyboard,
    balance_payments_keyboard,
    connect_keyboard,
    countries_keyboard,
    main_menu_keyboard,
    personal_cabinet_keyboard,
    payments_keyboard,
    setup_keyboard,
    tariffs_keyboard,
)
import httpx

from app.services.xui_client import XuiClient
from app.storage import (
    add_balance,
    clear_subscription,
    deduct_balance,
    ensure_user,
    get_referral_info,
    get_subscription,
    get_subscription_meta,
    get_vpn_data,
    record_first_payment,
    set_referrer,
    set_subscription,
)
from app.vpn_instructions import vpn_instructions
from app.config import get_miniapp_url, get_xui_settings

router = Router()
logger = logging.getLogger(__name__)

TARIFF_NAME = "Optimal"
TARIFF_PRICE = 150
TARIFF_DAYS = 30
TRIAL_DAYS = 3


@router.message(CommandStart())
async def start_handler(message: Message):
    ensure_user(message.from_user.id, message.from_user.username)
    payload = _extract_start_payload(message.text)
    if payload and payload.isdigit():
        set_referrer(message.from_user.id, int(payload))
    image_path = Path(__file__).resolve().parents[2] / "img" / "start.png"
    text = (
        "🐾 Привет! Это твой личный VPN‑сервис с котятами.\n"
        "🌐 Свободный интернет прямо в Telegram."
    )
    if image_path.exists():
        await message.answer_photo(
            FSInputFile(str(image_path)),
            caption=text,
            reply_markup=main_menu_keyboard(),
        )
    else:
        await message.answer(text, reply_markup=main_menu_keyboard())


def _tariffs_content() -> tuple[Path, str]:
    image_path = Path(__file__).resolve().parents[2] / "img" / "optimal.png"
    text = (
        f"💼 Тариф {TARIFF_NAME} — {TARIFF_PRICE} руб/мес.\n"
        "⚡ Подходит для ежедневного использования: стабильное подключение, "
        "быстрый доступ и поддержка популярных устройств.\n\n"
        "✨ Сейчас доступен один тариф, скоро добавим больше."
    )
    return image_path, text


@router.message(Command("tariffs"))
@router.message(lambda message: message.text in {"Тарифы", "💼 Тарифы"})
async def tariffs_handler(message: Message):
    image_path, text = _tariffs_content()
    if image_path.exists():
        await message.answer_photo(
            FSInputFile(str(image_path)),
            caption=text,
            reply_markup=tariffs_keyboard(),
        )
    else:
        await message.answer(text, reply_markup=tariffs_keyboard())


@router.message(Command("help"))
@router.message(lambda message: message.text in {"Help", "🧑‍💻 Help"})
async def help_handler(message: Message):
    await message.answer(
        "🧑‍💻 Саппорт: @nyxsupportvpn \n Время ответа ~2 часа",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("info"))
@router.message(lambda message: message.text in {"ℹ️ Информация", "Информация"})
async def info_handler(message: Message):
    image_path = Path(__file__).resolve().parents[2] / "img" / "info.png"
    text = (
        "ℹ️ Информация для пользователя\n\n"
        "Я программист-любитель и сделал этот сервис, потому что за безопасный "
        "и прозрачный интернет. Ниже вся ключевая информация.\n\n"
        "🗺️ Серверы: Финляндия, хостинг Aéza. Сейчас выдерживают ~20–30 "
        "пользователей в зависимости от нагрузки.\n"
        "⚡ Скорость (мое оборудование): 53 Мбит/с на загрузку и 80 Мбит/с "
        "на выгрузку. Ваша скорость зависит от устройства и базового интернета, "
        "поэтому возможны просадки.\n"
        "🔒 Безопасность: я вижу только объем трафика и не собираю данные о "
        "пользователях бота и подписках VPN.\n"
        "💳 Цена: формируется из окупаемости серверов, налогов и комиссий Telegram. "
        "Может показаться высокой, но для тех, кому VPN действительно нужен, "
        "это оправдано.\n"
        "💬 Если есть вопросы — напишите в поддержку."
    )
    if image_path.exists():
        await message.answer_photo(
            FSInputFile(str(image_path)),
            caption=text,
            reply_markup=main_menu_keyboard(),
        )
    else:
        await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(lambda message: message.text in {"⚙️ Настройка", "Настройка"})
async def setup_handler(message: Message):
    await message.answer(
        "Выберите приложение для настройки:", reply_markup=setup_keyboard()
    )


@router.callback_query(F.data == "back:setup")
async def setup_back(callback: CallbackQuery):
    if callback.message.photo:
        await callback.message.edit_caption(
            caption="Выберите приложение для настройки:",
            reply_markup=setup_keyboard(),
        )
    else:
        await callback.message.edit_text(
            "Выберите приложение для настройки:", reply_markup=setup_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data.startswith("setup:"))
async def setup_choice(callback: CallbackQuery):
    choice = callback.data.split(":", 1)[1]
    if choice == "v2raytun":
        text = (
            "V2rayTun\n\n"
            "1) Установите V2rayTun из App Store/Google Play.\n"
            "2) Откройте приложение и выберите импорт по ссылке.\n"
            "3) Вставьте свою VPN-ссылку и обновите список."
        )
    else:
        text = (
            "Happ\n\n"
            "1) Установите Happ из App Store/Google Play.\n"
            "2) В разделе подписок добавьте ссылку.\n"
            "3) Обновите профиль и подключитесь."
        )
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, reply_markup=setup_keyboard())
    else:
        await callback.message.edit_text(text, reply_markup=setup_keyboard())
    await callback.answer()


@router.message(Command("balance"))
@router.message(lambda message: message.text in {"Баланс", "💰 Баланс"})
async def balance_handler(message: Message):
    ensure_user(message.from_user.id, message.from_user.username)
    info = get_referral_info(message.from_user.id)
    balance = info.balance if info else 0
    referral_balance = info.referral_balance if info else 0
    text = f"💰 Баланс: {balance} ₽\n🤝 Реферальный счет: {referral_balance} ₽"
    await message.answer(text, reply_markup=balance_keyboard())


@router.message(lambda message: message.text == "Старт")
async def start_button_handler(message: Message):
    await start_handler(message)


@router.message(Command("ref"))
@router.message(lambda message: message.text in {"Пригласи друга", "🎁 Пригласи друга"})
async def referral_handler(message: Message):
    ensure_user(message.from_user.id, message.from_user.username)
    info = get_referral_info(message.from_user.id)
    bot = await message.bot.get_me()
    ref_link = f"https://t.me/{bot.username}?start={message.from_user.id}"
    invited_count = info.invited_count if info else 0
    referral_balance = info.referral_balance if info else 0
    image_path = Path(__file__).resolve().parents[2] / "img" / "ref.png"
    text = (
        "🎁 Приглашайте друзей и получайте 50% от их первой оплаты.\n"
        "Деньги поступают на реферальный счет и используются для подписки.\n\n"
        "💳 Минимальная сумма перевода на баланс: 150 ₽.\n"
        "📝 Вывод средств — по заявке (напишите в саппорт).\n\n"
        f"👥 Приглашенные: {invited_count}\n"
        f"🤝 Реферальный счет: {referral_balance} ₽\n\n"
        f"🔗 Ваша ссылка: {ref_link}"
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
    if not text:
        return None
    if not text.startswith("/start"):
        return None
    parts = text.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else None


@router.callback_query(F.data == "tariff:connect")
async def connect_tariff(callback: CallbackQuery):
    text = "🌍 Выберите страну для покупки:"
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text, reply_markup=countries_keyboard()
        )
    else:
        await callback.message.edit_text(text, reply_markup=countries_keyboard())
    await callback.answer()


@router.callback_query(F.data == "tariff:trial")
async def trial_tariff(callback: CallbackQuery):
    ensure_user(callback.from_user.id, callback.from_user.username)
    _, _, xui_end_at = await _fetch_xui_subscription(callback.from_user, "fi")
    end_at = xui_end_at
    if not end_at:
        _, end_at = get_subscription(callback.from_user.id)
    end_at = _normalize_dt(end_at)
    if end_at and end_at >= datetime.now(timezone.utc):
        await callback.message.answer(
            "✅ У вас уже есть активная подписка.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    username = callback.from_user.username or f"tg_{callback.from_user.id}"
    email = f"@{username}"
    xui = XuiClient.from_settings(get_xui_settings("nl"))
    try:
        await xui.login()
        sub_id = await xui.add_client(email=email, days=TRIAL_DAYS)
        sub_link = xui.subscription_link(sub_id)
    except httpx.TimeoutException:
        await callback.message.answer(
            "⚠️ Сервис подписок временно недоступен. Попробуйте чуть позже.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return
    except RuntimeError:
        await callback.answer()
        return
    finally:
        await xui.close()

    instructions = vpn_instructions(sub_link)
    link_image = Path(__file__).resolve().parents[2] / "img" / "link.png"
    if link_image.exists():
        await callback.bot.send_photo(
            callback.from_user.id,
            FSInputFile(str(link_image)),
            caption=instructions,
            reply_markup=connect_keyboard(get_miniapp_url()),
        )
    else:
        await callback.bot.send_message(
            callback.from_user.id,
            instructions,
            reply_markup=connect_keyboard(get_miniapp_url()),
            disable_web_page_preview=True,
        )

    start_at = datetime.now(timezone.utc)
    end_at = start_at + timedelta(days=TRIAL_DAYS)
    set_subscription(
        callback.from_user.id,
        start_at,
        end_at,
        sub_link,
        instructions,
        "nl",
    )
    await callback.message.answer(
        "🎉 Пробный период на 3 дня активирован.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay:balance:"))
async def pay_handler(callback: CallbackQuery):
    country = callback.data.split(":", 2)[2]
    if country not in {"nl"}:
        await callback.answer()
        return
    ensure_user(callback.from_user.id, callback.from_user.username)
    if not deduct_balance(callback.from_user.id, TARIFF_PRICE):
        await callback.message.answer(
            "❌ Недостаточно средств. Пополните баланс и попробуйте снова.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return
    username = callback.from_user.username or f"tg_{callback.from_user.id}"
    email = f"@{username}"
    settings = get_xui_settings(country)
    xui = XuiClient.from_settings(settings)
    try:
        await xui.login()
        sub_id = await xui.add_client(email=email, days=TARIFF_DAYS)
        sub_link = xui.subscription_link(sub_id)
    except httpx.TimeoutException:
        add_balance(callback.from_user.id, TARIFF_PRICE)
        await callback.message.answer(
            "⚠️ Сервис подписок временно недоступен. Попробуйте чуть позже.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return
    except RuntimeError:
        add_balance(callback.from_user.id, TARIFF_PRICE)
        await callback.answer()
        return
    except Exception:
        add_balance(callback.from_user.id, TARIFF_PRICE)
        await callback.answer()
        return
    finally:
        await xui.close()
    instructions = vpn_instructions(sub_link)
    link_image = Path(__file__).resolve().parents[2] / "img" / "link.png"
    if link_image.exists():
        await callback.bot.send_photo(
            callback.from_user.id,
            FSInputFile(str(link_image)),
            caption=instructions,
            reply_markup=main_menu_keyboard(),
        )
    else:
        await callback.bot.send_message(
            callback.from_user.id,
            instructions,
            reply_markup=main_menu_keyboard(),
            disable_web_page_preview=True,
        )
    start_at = datetime.now(timezone.utc)
    end_at = start_at + timedelta(days=TARIFF_DAYS)
    set_subscription(
        callback.from_user.id,
        start_at,
        end_at,
        sub_link,
        instructions,
        country,
    )
    if record_first_payment(callback.from_user.id, TARIFF_PRICE):
        logger.info(
            "Referral reward credited for tg_id=%s",
            callback.from_user.id,
        )
    await callback.answer()


async def _personal_cabinet_text(user) -> tuple[str, bool]:
    ensure_user(user.id, user.username)
    meta = get_subscription_meta(user.id)
    country = "nl"
    if meta and isinstance(meta.get("country"), str):
        country = meta["country"]
    xui_available, xui_link, xui_end_at = await _fetch_xui_subscription(user, country)
    if xui_available and not xui_link and not xui_end_at:
        clear_subscription(user.id)
        return "❌ Подписка не активна", False
    subscription_link, instructions = get_vpn_data(user.id)
    if xui_available and xui_link:
        subscription_link = xui_link
        instructions = vpn_instructions(xui_link)
    elif subscription_link and not instructions:
        instructions = vpn_instructions(subscription_link)

    end_at = xui_end_at
    if not end_at:
        _, end_at = get_subscription(user.id)
    end_at = _normalize_dt(end_at)
    if not end_at or end_at < datetime.now(timezone.utc):
        return "❌ Подписка не активна", False
    end_str = end_at.strftime("%d.%m.%Y")
    if instructions:
        return f"✅ Активна до {end_str}\n\n{instructions}", True
    return f"✅ Активна до {end_str}", True


async def _fetch_xui_subscription(
    user, country: str
) -> tuple[bool, str | None, datetime | None]:
    email = _email_for_user(user)
    try:
        settings = get_xui_settings(country)
        xui = XuiClient.from_settings(settings)
    except RuntimeError:
        return False, None, None
    try:
        await xui.login()
        result = await xui.get_client_subscription(email)
        if not result:
            return True, None, None
        sub_id, end_at = result
        return True, xui.subscription_link(sub_id), end_at
    except Exception:
        return False, None, None
    finally:
        await xui.close()


def _email_for_user(user) -> str:
    username = user.username or f"tg_{user.id}"
    return f"@{username}"


def _normalize_dt(value: datetime | None) -> datetime | None:
    if not value:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@router.callback_query(F.data.startswith("country:"))
async def choose_country(callback: CallbackQuery):
    country_map = {
        "nl": "🇳🇱 Сервер Netherlands выбран.",
    }
    code = callback.data.split(":", 1)[1]
    text = (
        country_map.get(code, "✅ Сервер выбран.") + "\nОплата с баланса доступна ниже."
    )
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text, reply_markup=payments_keyboard(code)
        )
    else:
        await callback.message.edit_text(text, reply_markup=payments_keyboard(code))
    await callback.answer()


@router.callback_query(F.data == "balance:topup")
async def balance_topup(callback: CallbackQuery):
    await callback.message.answer(
        "⚠️ Пополнение баланса временно недоступно.",
        reply_markup=balance_payments_keyboard(),
    )
    await callback.answer()


@router.message(lambda message: message.text in {"Личный кабинет", "👤 Личный кабинет"})
async def personal_cabinet_handler(message: Message):
    image_path = Path(__file__).resolve().parents[2] / "img" / "profile.png"
    caption, is_active = await _personal_cabinet_text(message.from_user)
    keyboard = personal_cabinet_keyboard(show_buy=not is_active)
    if image_path.exists():
        await message.answer_photo(
            FSInputFile(str(image_path)),
            caption=caption,
            reply_markup=keyboard,
        )
    else:
        await message.answer(caption, reply_markup=keyboard)


@router.callback_query(F.data == "balance:open")
async def balance_open(callback: CallbackQuery):
    ensure_user(callback.from_user.id, callback.from_user.username)
    info = get_referral_info(callback.from_user.id)
    balance = info.balance if info else 0
    referral_balance = info.referral_balance if info else 0
    text = f"💰 Баланс: {balance} ₽\n🤝 Реферальный счет: {referral_balance} ₽"
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text, reply_markup=balance_keyboard()
        )
    else:
        await callback.message.edit_text(text, reply_markup=balance_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back:cabinet")
async def back_to_cabinet(callback: CallbackQuery):
    caption, is_active = await _personal_cabinet_text(callback.from_user)
    keyboard = personal_cabinet_keyboard(show_buy=not is_active)
    if callback.message.photo:
        await callback.message.edit_caption(caption=caption, reply_markup=keyboard)
    else:
        await callback.message.edit_text(caption, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "cabinet:buy")
async def cabinet_buy(callback: CallbackQuery):
    image_path, text = _tariffs_content()
    if image_path.exists():
        await callback.message.answer_photo(
            FSInputFile(str(image_path)),
            caption=text,
            reply_markup=tariffs_keyboard(),
        )
    else:
        await callback.message.answer(text, reply_markup=tariffs_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back:balance")
async def back_to_balance(callback: CallbackQuery):
    image_path = Path(__file__).resolve().parents[2] / "img" / "balance.png"
    info = get_referral_info(callback.from_user.id)
    balance = info.balance if info else 0
    referral_balance = info.referral_balance if info else 0
    text = f"💰 Баланс: {balance} ₽\n🤝 Реферальный счет: {referral_balance} ₽"
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text, reply_markup=balance_keyboard()
        )
    else:
        await callback.message.edit_text(text, reply_markup=balance_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back:tariffs")
async def back_to_tariffs(callback: CallbackQuery):
    image_path, text = _tariffs_content()
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text, reply_markup=tariffs_keyboard()
        )
    else:
        await callback.message.edit_text(text, reply_markup=tariffs_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back:countries")
async def back_to_countries(callback: CallbackQuery):
    text = "🌍 Выберите страну для покупки:"
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text, reply_markup=countries_keyboard()
        )
    else:
        await callback.message.edit_text(text, reply_markup=countries_keyboard())
    await callback.answer()
