import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_bot_token
from app.config import get_required_channel_id
from app.middleware.required_channel import RequireChannelMiddleware
from app.notifications import notify_subscriptions
from app.preflight import run_preflight
from app.storage import init_db, purge_expired_subscriptions


async def main():
    logging.basicConfig(level=logging.INFO)
    token = get_bot_token()

    await run_preflight()
    init_db()
    bot = Bot(token=token)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(purge_expired_subscriptions, "interval", hours=12)
    scheduler.add_job(notify_subscriptions, "interval", hours=6, args=[bot])
    scheduler.start()

    from app.handlers import payments, start, subscription

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start"),
            BotCommand(command="help", description="Help"),
            BotCommand(command="info", description="Info"),
        ]
    )
    dp = Dispatcher()
    dp.message.middleware(RequireChannelMiddleware(get_required_channel_id()))
    dp.callback_query.middleware(RequireChannelMiddleware(get_required_channel_id()))
    dp.include_router(start.router)
    dp.include_router(subscription.router)
    dp.include_router(payments.router)
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
