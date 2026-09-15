import logging
import ssl
from email.message import EmailMessage

import aiosmtplib
import certifi

from app.config import get_smtp_settings

logger = logging.getLogger(__name__)


async def send_payment_notification(username: str, tg_id: int) -> bool:
    """Отправить уведомление админу о новой оплате."""
    settings = get_smtp_settings()

    message = EmailMessage()
    message["From"] = settings["login"]
    message["To"] = settings["to_email"]
    message["Subject"] = "💰 Новая оплата в боте!"

    body = (
        f"Дмитрий, вам пришла оплата — посмотрите Telegram.\n\n"
        f"От пользователя: {username}\n"
        f"ID: {tg_id}"
    )
    message.set_content(body)

    try:
        tls_context = ssl.create_default_context(cafile=certifi.where())
        await aiosmtplib.send(
            message,
            hostname=settings["host"],
            port=settings["port"],
            username=settings["login"],
            password=settings["password"],
            start_tls=True,
            tls_context=tls_context,
        )
        logger.info("Payment notification email sent for tg_id=%s", tg_id)
        return True
    except Exception:
        logger.exception("Failed to send payment notification email for tg_id=%s", tg_id)
        return False
