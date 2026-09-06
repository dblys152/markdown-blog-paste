import asyncio
import smtplib
import ssl
from collections.abc import Callable
from email.message import EmailMessage
from types import TracebackType
from typing import Protocol, Self

from md2blog.modules.identity.application.port.outbound.email import (
    EmailDeliveryError,
    OutboundEmail,
)

SMTP_TIMEOUT_SECONDS = 10.0


class SmtpClient(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def ehlo(self) -> object: ...

    def starttls(self, *, context: ssl.SSLContext) -> object: ...

    def login(self, username: str, password: str) -> object: ...

    def send_message(self, message: EmailMessage) -> object: ...


SmtpClientFactory = Callable[[str, int, float], SmtpClient]


def create_smtp_client(host: str, port: int, timeout: float) -> SmtpClient:
    return smtplib.SMTP(host=host, port=port, timeout=timeout)


class GmailSmtpEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        from_address: str,
        client_factory: SmtpClientFactory = create_smtp_client,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_address = from_address
        self._client_factory = client_factory

    async def send(self, message: OutboundEmail) -> None:
        await asyncio.to_thread(self._send, message)

    def _send(self, outbound: OutboundEmail) -> None:
        message = EmailMessage()
        message["From"] = self._from_address
        message["To"] = outbound.to.value
        message["Subject"] = outbound.subject
        message.set_content(outbound.html, subtype="html")

        try:
            with self._client_factory(self._host, self._port, SMTP_TIMEOUT_SECONDS) as client:
                client.ehlo()
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
                client.login(self._username, self._password)
                client.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise EmailDeliveryError from error
