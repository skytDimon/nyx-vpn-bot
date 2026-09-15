"""Панель -> БД: если у email есть '@' -> в pending по username; id подтянется на /start.

Кабинет покажет подписку только после того, как юзер зайдёт в бота (тогда
pending перенесётся в subscriptions с его tg_id).
@tg_{id} -> сразу в subscriptions (известный tg_id, без ожидания).
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import re
import sys
from datetime import datetime, timezone

from app.config import load_env
from app.services.xui_client import XuiClient
from app.storage import ensure_user, set_subscription, upsert_pending_subscription
from app.vpn_instructions import vpn_instructions

logger = logging.getLogger(__name__)

_RE_TG_ID = re.compile(r"^@tg_(\d+)$", re.IGNORECASE)


def _parse_at_username(email: str) -> str | None:
    if "@" not in email:
        return None
    at = email.find("@")
    cand = email[at + 1 :].strip()
    if not cand or "@" in cand:
        return None
    # Разрешаем telegram-совместимые и короткие имена (панель часто ставит короткие)
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,31}", cand):
        return None
    return cand


async def main() -> int:
    p = argparse.ArgumentParser(description="Синхронизировать клиентов панели -> pending/subscriptions")
    p.add_argument("--apply", action="store_true", help="Писать в БД (без флага — dry-run)")
    args = p.parse_args()

    load_env()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    client = XuiClient.from_env()
    try:
        await client.login()
        raw_clients = await client.list_all_clients()
    except Exception as e:
        logger.error("XUI: %s", e)
        print(f"[XUI error] {e}", file=sys.stderr)
        try:
            await client.close()
        except Exception:
            pass
        return 2

    by_email: dict[str, dict] = {}
    for c in raw_clients:
        if c["email"] not in by_email:
            by_email[c["email"]] = c

    if not by_email:
        print("Панель: клиентов на настроенных inbound'ах нет.")
        await client.close()
        return 0

    rows: list[tuple[str, str, str | None, datetime | None, str | None, str]] = []
    # email, action(write_pending/write_direct/skip), tg_s, end_at, sub_id, note

    for email, c in sorted(by_email.items()):
        sub_id = (c.get("subId") or "").strip()
        expiry_ms = int(c.get("expiryTime") or 0)
        end_at = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc) if expiry_ms else None
        if not sub_id or not end_at:
            rows.append((email, "skip", None, end_at, sub_id, "no subId/expiry"))
            continue
        m = _RE_TG_ID.match(email)
        if m:
            rows.append((email, "direct", m.group(1), end_at, sub_id, f"@tg_ -> tg_id {m.group(1)}"))
            continue
        cand = _parse_at_username(email)
        if cand is None:
            if "@" in email:
                rows.append((email, "skip", None, end_at, sub_id, "есть @ но юзернейм невалидный"))
            else:
                rows.append((email, "skip", None, end_at, sub_id, "нет @ — пропускаем"))
            continue
        rows.append((email, "pending", cand, end_at, sub_id, f"pending username={cand}"))

    w = 38
    hdr = f"{'email':{w}}  {'target':16}  {'end_at':10}  action                note"
    print(hdr)
    print("-" * len(hdr))
    pending_n = direct_n = skipped = 0
    for email, action, target, end_at, sub_id, note in rows:
        end_s = end_at.strftime("%Y-%m-%d") if end_at else "—"
        tgt = (target or "—")
        label = {"pending": "pending", "direct": "direct", "skip": "skip"}[action]
        if action == "pending":
            pending_n += 1
        elif action == "direct":
            direct_n += 1
        else:
            skipped += 1
        print(f"{email:{w}}  {tgt:16}  {end_s:10}  {label:20}  [{note}]")

    if not args.apply:
        print()
        print(f"DRY-RUN: всего {len(by_email)}, pending={pending_n}, direct={direct_n}, skip={skipped}")
        print("Чтобы записать:  docker compose -f docker/docker-compose.yml exec bot python -m app.sync_panel --apply")
        await client.close()
        return 0

    now = datetime.now(timezone.utc)
    done_pending = done_direct = err = 0
    for email, action, target, end_at, sub_id, _ in rows:
        if action == "skip" or not end_at or not sub_id:
            continue
        link = client.subscription_link(sub_id)
        instructions = vpn_instructions(link)
        try:
            if action == "pending":
                assert target is not None
                upsert_pending_subscription(target, email, now, end_at, link, instructions, "nl", client_uuid=email, sub_id=sub_id)
                done_pending += 1
            elif action == "direct":
                tg_id = int(target)  # type: ignore[arg-type]
                ensure_user(tg_id, None)
                set_subscription(tg_id, now, end_at, link, instructions, "nl", client_uuid=email, sub_id=sub_id)
                done_direct += 1
        except Exception as e:
            logger.exception("write %s: %s", email, e)
            err += 1

    print()
    print(f"APPLY: pending записано {done_pending}, direct {done_direct}, skip {skipped}, ошибок {err}")
    await client.close()
    return 1 if err else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
