from urllib.parse import quote

from md2blog.modules.identity.application.port.outbound.email import (
    EmailSender,
    OutboundEmail,
)
from md2blog.modules.identity.domain.value_objects import Email
from md2blog.shared.application.event_ports import SensitiveValueCipher


class EmailVerificationMessageHandler:
    def __init__(self, sender: EmailSender, cipher: SensitiveValueCipher) -> None:
        self._sender = sender
        self._cipher = cipher

    async def handle(self, payload: dict[str, str]) -> None:
        await _send_account_confirmation_email(payload, self._sender, self._cipher)


class PasswordResetMessageHandler:
    def __init__(self, sender: EmailSender, cipher: SensitiveValueCipher) -> None:
        self._sender = sender
        self._cipher = cipher

    async def handle(self, payload: dict[str, str]) -> None:
        await _send_account_confirmation_email(payload, self._sender, self._cipher)


async def _send_account_confirmation_email(
    payload: dict[str, str],
    sender: EmailSender,
    cipher: SensitiveValueCipher,
) -> None:
    token = cipher.decrypt(payload["encrypted_token"])
    action_url = f"{payload['action_url']}?token={quote(token, safe='')}"
    html = (
        f"<p>{payload['introduction_html']}</p>"
        f'<p><a href="{action_url}">{payload["action_label"]}</a></p>'
        "<p>본인이 요청하지 않았다면 이 메일을 무시해 주세요.</p>"
    )
    await sender.send(
        OutboundEmail(
            to=Email(payload["to"]),
            subject=payload["subject"],
            html=html,
        )
    )
