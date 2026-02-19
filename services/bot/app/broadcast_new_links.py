import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.config import get_bot_token
from app.storage import fetch_users_with_subscription_links


async def main() -> int:
    bot = Bot(token=get_bot_token())
    success = 0
    blocked = 0
    failed = 0

    for row in fetch_users_with_subscription_links(min_days=3, max_days=30):
        tg_id = int(row["tg_id"])
        link = row["subscription_link"]
        if not link:
            continue
        text = (
            "Мы перешли на новый, более быстрый сервер, вот ваша новая ссылка -> "
            f"{link}"
        )
        try:
            await bot.send_message(tg_id, text)
            success += 1
        except TelegramForbiddenError:
            blocked += 1
        except TelegramBadRequest:
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await bot.session.close()
    logging.info(
        "Broadcast done. success=%s blocked=%s failed=%s", success, blocked, failed
    )
    print(f"Broadcast done. success={success} blocked={blocked} failed={failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
