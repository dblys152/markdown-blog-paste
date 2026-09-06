from email.message import EmailMessage
from typing import Self

import pytest

from md2blog.modules.identity.application.port.outbound.email import OutboundEmail
from md2blog.modules.identity.domain.value_objects import Email
from md2blog.modules.identity.infrastructure.email import GmailSmtpEmailSender


class FakeSmtpClient:
    def __init__(self) -> None:
        self.started_tls = False
        self.login_credentials: tuple[str, str] | None = None
        self.message: EmailMessage | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def ehlo(self) -> None:
        pass

    def starttls(self, *, context: object) -> None:
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        self.login_credentials = (username, password)

    def send_message(self, message: EmailMessage) -> None:
        self.message = message


@pytest.mark.asyncio
async def test_gmail_sender_uses_tls_and_authenticated_smtp() -> None:
    client = FakeSmtpClient()
    sender = GmailSmtpEmailSender(
        host="smtp.gmail.com",
        port=587,
        username="sender@gmail.com",
        password="app-password",
        from_address="MD2Blog <sender@gmail.com>",
        client_factory=lambda _host, _port, _timeout: client,
    )

    await sender.send(
        OutboundEmail(
            to=Email("receiver@example.com"),
            subject="이메일 인증",
            html="<p>인증해 주세요.</p>",
        )
    )

    assert client.started_tls
    assert client.login_credentials == ("sender@gmail.com", "app-password")
    assert client.message is not None
    assert client.message["From"] == "MD2Blog <sender@gmail.com>"
    assert client.message["To"] == "receiver@example.com"
    assert client.message["Subject"] == "이메일 인증"
    assert client.message.get_body(preferencelist=("html",)).get_content().strip() == (
        "<p>인증해 주세요.</p>"
    )
