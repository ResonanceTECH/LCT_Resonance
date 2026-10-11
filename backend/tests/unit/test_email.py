import logging
import smtplib
from email.message import EmailMessage

import pytest

from app.core.config import get_settings
from app.core.errors import AppError
from app.integrations import email as email_integration

TOKEN = "t" * 40


@pytest.fixture
def settings(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "app_env", "dev")
    monkeypatch.setattr(settings, "smtp_host", "")
    monkeypatch.setattr(settings, "public_api_url", "http://api.test/")
    return settings


@pytest.fixture
def sent(monkeypatch) -> list[EmailMessage]:
    messages: list[EmailMessage] = []
    monkeypatch.setattr(email_integration, "_send_smtp_message", messages.append)
    return messages


@pytest.fixture
def email_log(caplog, monkeypatch):
    # The app logger stops propagating once the app configures logging, so attach directly
    # and stop propagation here too: each record is then captured exactly once.
    logger = logging.getLogger("app.email")
    monkeypatch.setattr(logger, "propagate", False)
    logger.addHandler(caplog.handler)
    yield caplog
    logger.removeHandler(caplog.handler)


@pytest.mark.asyncio
async def test_dev_without_smtp_logs_the_link_instead_of_sending(settings, sent, email_log):
    await email_integration.send_verification_email(email="a@b.ru", token=TOKEN)
    assert sent == []
    [record] = email_log.records
    assert record.verification_url == (
        f"http://api.test/api/auth/verify-email/confirm?token={TOKEN}"
    )


@pytest.mark.asyncio
async def test_prod_without_smtp_refuses(settings, sent):
    settings.app_env = "prod"
    with pytest.raises(AppError) as error:
        await email_integration.send_verification_email(email="a@b.ru", token=TOKEN)
    assert error.value.code == "EMAIL_DELIVERY_UNAVAILABLE"


@pytest.mark.asyncio
async def test_smtp_sends_the_confirmation_link(settings, sent):
    settings.smtp_host = "smtp.test"
    await email_integration.send_verification_email(email="a@b.ru", token=TOKEN)
    [message] = sent
    assert message["To"] == "a@b.ru"
    assert f"http://api.test/api/auth/verify-email/confirm?token={TOKEN}" in message.get_content()


@pytest.mark.asyncio
async def test_smtp_failure_is_logged_with_the_reason(settings, monkeypatch, email_log):
    settings.smtp_host = "smtp.test"

    def refuse(_message):
        raise smtplib.SMTPAuthenticationError(535, b"authentication failed")

    monkeypatch.setattr(email_integration, "_send_smtp_message", refuse)
    with pytest.raises(AppError) as error:
        await email_integration.send_verification_email(email="a@b.ru", token=TOKEN)
    assert (error.value.code, error.value.status_code) == ("EMAIL_DELIVERY_FAILED", 503)
    assert "authentication failed" in email_log.records[0].error
