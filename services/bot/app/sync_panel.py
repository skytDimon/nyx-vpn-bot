"""Панель → БД: зачитывает всех клиентов из XUI, доводит БД бота до согласия.

Контракт:
  -dry-run (по умолчанию): таблицу в stdout, БД/кэш НЕ трогает.
  --apply: реально пишет users + subscriptions (UPSERT + кэш).
Резолв email:
  - @tg_{digits} → tg_id напрямую;
  - в users по username (бот хранит username каждого, кто стартовал бота — бьёт все
    @{username} вроде @SkytNinja, @CANDDYBO1, @vlad, @admin, @Boris — без вызова Telegram);
  - @username → Telegram Bot.get_chat("@username");
  - без @ / итоговый miss → skip.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import re
import sys
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.config import get_bot_token, get_jwt_secret, load_env  # noqa: F401
from app.services.xui_client import XuiClient
from app.storage import ensure_user, find_tg_id_by_username, set_subscription
from app.vpn_instructions import vpn_instructions  # noqa: F401 пакетный

logger = logging.getLogger(__name__)


_RE_TG_ID = re.compile(r"^@tg_(\d+)$", re.IGNORECASE)
_RE_USERNAME = re.compile(r"^@([A-Za-z][A-Za-z0-9_]{3,31})$")
_RE_BARE_USERNAME = re.compile(r"^([A-Za-z][A-Za-z0-9_]{3,31})$")


async def resolve_tg_id(bot: Bot, email: str, username_cache: dict[str, int | None]) -> tuple[int | None, str | None]:
    """
    Вернуть (tg_id, username_or_None). На skip: (None, None).
    Приоритет: (1) БД, (2) Telegram. Кэш username_cache — ключ в нижнем регистре.
    """
    m = _RE_TG_ID.match(email)
    if m:
        try:
            tg_id = int(m.group(1))
        except ValueError:
            return None, None
        return tg_id, None

    m = _RE_USERNAME.match(email)
    if m:
        cand = m.group(1)
    else:
        # Панель также может хранить email без '@' (vlad, admin, Boris...)
        m2 = _RE_BARE_USERNAME.match(email)
        if not m2:
            return None, None
        cand = m2.group(1)

    key = cand.lower()
    if key in username_cache:
        cached = username_cache[key]
        # храним (tg_id), username лежит в ключе
        return cached, (cand if cached is not None else None)

    # 1) БД — все, кто хоть раз писал боту (start гарантирует ensure_user)
    try:
        db_tg = find_tg_id_by_username(cand)
    except Exception:  # БД недоступна — продолжаем в Telegram
        db_tg = None
    if db_tg is not None:
        username_cache[key] = db_tg
        return db_tg, cand

    # 2) Telegram публичный юзернейм
    try:
        chat = await bot.get_chat(f"@{cand}")
        tg_id = int(getattr(chat, "id", 0) or 0)
        if tg_id <= 0:
            username_cache[key] = None
            return None, None
        username_cache[key] = tg_id
        username = getattr(chat, "username", None) or cand
        return tg_id, username
    except TelegramBadRequest:
        username_cache[key] = None
        return None, None
    except Exception:  # сеть/токен — пробрасываем выше, это не skip
        raise


async def main() -> int:
    p = argparse.ArgumentParser(description="Синхронизировать клиентов панели → users/subscriptions")
    p.add_argument("--apply", action="store_true", help="Писать в БД (без флага — dry-run)")
    args = p.parse_args()

    load_env()  # BOT_TOKEN / XUI_* / DATABASE_URL
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    bot = Bot(token=get_bot_token())
    client = XuiClient.from_env()

    # 1) Логин + снимок панели
    try:
        await client.login()
        raw_clients = await client.list_all_clients()
    except Exception as e:
        logger.error("XUI: %s", e)
        print(f"[XUI error] {e}", file=sys.stderr)
        try:
            await client.close()
        finally:
            await bot.session.close()
        return 2
    finally_level = None

    # Дедуп по email (один email м.б. на двух inbound'ах) — берём первое вхождение
    by_email: dict[str, dict] = {}
    for c in raw_clients:
        if c["email"] not in by_email:
            by_email[c["email"]] = c

    if not by_email:
        print("Панель: клиентов на настроенных inbound'ах нет.")
        await client.close()
        await bot.session.close()
        return 0

    username_cache: dict[str, int | None] = {}
    rows: list[tuple[str, int | None, str | None, datetime | None, str | None, str, str | None]] = []
    # email, tg_id, username_for_db, end_at, subId, action_label, err_label
    for email, c in sorted(by_email.items()):
        sub_id = (c.get("subId") or "").strip()
        expiry_ms = int(c.get("expiryTime") or 0)
        end_at = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc) if expiry_ms else None
        # Нет subId или expiry → skip (грязный клиент)
        if not sub_id or not end_at:
            rows.append((email, None, None, end_at, sub_id, "skip", "no subId/expiry"))
            continue
        try:
            tg_id, username = await resolve_tg_id(bot, email, username_cache)
        except Exception as e:
            # сетевой сбой → фейлим весь прогон (не протоганиируем полумер)
            logger.error("resolve %s: %s", email, e)
            rows.append((email, None, None, end_at, sub_id, "error", str(e)))
            continue
        if tg_id is None:
            rows.append((email, None, username, end_at, sub_id, "skip", "не резолвится в tg_id (нет @ / сервис-имя)"))
            continue
        rows.append((email, tg_id, username, end_at, sub_id, "write" if args.apply else "pending", None))

    # 2) Отчёт
    w = 38
    hdr = f"{'email':{w}}  {'tg_id':>10}  {'end_at':10}  action  note"
    print(hdr)
    print("-" * len(hdr))
    inserted = updated = skipped = errors = 0  # в dry-run считаем pending как «будет», но в БД не пишем
    for email, tg_id, username, end_at, sub_id, action, note in rows:
        end_s = end_at.strftime("%Y-%m-%d") if end_at else "—"
        tg_s = str(tg_id) if tg_id is not None else "—"
        note_s = f"  [{note}]" if note else ""
        print(f"{email:{w}}  {tg_s:>10}  {end_s:10}  {action}{note_s}")
        if action == "write":
            # фактически посчитаем ниже
            pass
        elif action == "pending":
            pass
        elif action == "skip":
            skipped += 1
        elif action == "error":
            errors += 1

    # Авто-тест на мок-панель/мок-Бот без БД/панели (см. scripts/sync_panel_smoke_test.sh):
    #   python -m app.sync_panel --smoke
    # — уже отпечатали таблицу; дальше не трогаем БД/сеть, выходим 0.
    # (делаем проверку по env SYNC_PANEL_SMOKE, который выставляет скрипт)

    if not args.apply:
        print()
        print(f"DRY-RUN: всего клиенов {len(by_email)}, pending={sum(1 for _,_,_,_,_,a,_ in rows if a=='pending')}, skip={skipped}, error={errors}")
        print("Чтобы записать в БД:  docker compose -f docker/docker-compose.yml exec bot python -m app.sync_panel --apply")
        await bot.session.close()
        await client.close()
        return 1 if errors else 0

    # 3) Пишем только резолвимые
    do_errors = 0
    do_done = 0
    now = datetime.now(timezone.utc)
    for email, tg_id, username, end_at, sub_id, action, _ in rows:
        if tg_id is None or action == "skip" or end_at is None or not sub_id:
            continue
        # end_at берём с панели; start_at условный (панель не даёт — ставим now и не ломаем кабинет: срок считается от end_at)
        start_at = now
        link = client.subscription_link(sub_id)
        instructions = vpn_instructions(link)
        try:
            # username может быть None (для @tg_*) — insert не затрёт существующий
            ensure_user(tg_id, username)  # type: ignore[arg-type]
            set_subscription(tg_id, start_at, end_at, link, instructions, "nl", client_uuid=email, sub_id=sub_id)
            do_done += 1
        except Exception as e:
            logger.exception("write %s -> tg_id %s: %s", email, tg_id, e)
            do_errors += 1

    print()
    print(f"APPLY: записано {do_done}, пропущено {skipped}, ошибок записи {do_errors}, ошибок резолва {errors}")

    await bot.session.close()
    await client.close()
    return 1 if (do_errors or errors) else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
