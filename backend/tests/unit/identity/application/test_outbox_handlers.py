import pytest

from md2blog.modules.identity.application.outbox_handlers import (
    EmailVerificationMessageHandler,
    PasswordResetMessageHandler,
)
from md2blog.modules.identity.application.port.outbound.email import OutboundEmail


class RecordingEmailSender:
    def __init__(self) -> None:
        self.messages: list[OutboundEmail] = []

    async def send(self, message: OutboundEmail) -> None:
        self.messages.append(message)


class ReversingCipher:
    def encrypt(self, value: str) -> str:
        return value[::-1]

    def decrypt(self, encrypted_value: str) -> str:
        return encrypted_value[::-1]


def email_payload() -> dict[str, str]:
    return {
        "to": "user@example.com",
        "subject": "인증",
        "introduction_html": "사용자님, 인증해 주세요.",
        "action_label": "인증하기",
        "action_url": "https://md2blog.test/verify-email",
        "encrypted_token": "nekot terces",
    }


@pytest.mark.asyncio
async def test_email_verification_handler_decrypts_token_and_sends_email() -> None:
    sender = RecordingEmailSender()
    handler = EmailVerificationMessageHandler(sender, ReversingCipher())

    await handler.handle(email_payload())

    email = sender.messages[0]
    assert email.to.value == "user@example.com"
    assert email.subject == "인증"
    assert "token=secret%20token" in email.html


@pytest.mark.asyncio
async def test_password_reset_handler_decrypts_token_and_sends_email() -> None:
    sender = RecordingEmailSender()
    handler = PasswordResetMessageHandler(sender, ReversingCipher())
    payload = email_payload()
    payload["action_url"] = "https://md2blog.test/reset-password"

    await handler.handle(payload)

    assert "reset-password?token=secret%20token" in sender.messages[0].html
