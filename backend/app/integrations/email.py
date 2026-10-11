from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

from app.core.config import get_settings
from app.core.errors import AppError

logger = logging.getLogger("app.email")


def ensure_email_delivery_available() -> None:
    settings = get_settings()
    if not settings.smtp_host and not settings.is_dev:
        raise AppError(
            "EMAIL_DELIVERY_UNAVAILABLE",
            "Отправка писем не настроена, обратитесь к администратору",
            503,
        )


def _send_smtp_message(message: EmailMessage) -> None:
    settings = get_settings()
    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_sec,
        ) as smtp:
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        return

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=settings.smtp_timeout_sec,
    ) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


async def send_verification_email(*, email: str, token: str) -> None:
    settings = get_settings()
    ensure_email_delivery_available()
    url = (
        f"{settings.public_api_url.rstrip('/')}/api/auth/verify-email/confirm"
        f"?token={quote(token, safe='')}"
    )
    if not settings.smtp_host:
        # Dev without SMTP: nothing is sent, so the link goes to the console instead. The token
        # is fine to log here: dev already returns it in the X-Verification-Token header.
        logger.warning(
            "email_not_sent: SMTP_HOST is empty, open the verification link manually",
            extra={"verification_url": url},
        )
        return

    message = EmailMessage()
    message["Subject"] = "Подтвердите адрес электронной почты"
    message["From"] = settings.smtp_from_email
    message["To"] = email
    message.set_content(
        "Здравствуйте!\n\n"
        "Чтобы подтвердить адрес электронной почты, откройте ссылку и нажмите кнопку подтверждения:\n"
        f"{url}\n\n"
        "Если вы не создавали аккаунт, проигнорируйте это письмо."
    )

    try:
        await asyncio.to_thread(_send_smtp_message, message)
    except (OSError, smtplib.SMTPException) as exc:
        # SMTP errors carry the server's reply (e.g. "535 authentication failed"), never the
        # password, and are the only clue to a misconfigured SMTP_*.
        logger.warning("verification_email_failed", extra={"error": repr(exc)})
        raise AppError(
            "EMAIL_DELIVERY_FAILED",
            "Не удалось отправить письмо, попробуйте позже",
            503,
        ) from exc
