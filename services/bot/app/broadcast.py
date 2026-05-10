import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.config import get_bot_token
from app.storage import fetch_all_user_ids


async def main() -> int:
    message = " ".join(sys.argv[1:]).strip()
    if not message:
        print('Usage: python -m app.broadcast "your message"')
        return 1

    bot = Bot(token=get_bot_token())
    success = 0
    blocked = 0
    failed = 0

    for tg_id in fetch_all_user_ids():
        try:
            await bot.send_message(tg_id, message)
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
