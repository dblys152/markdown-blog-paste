from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GeneratedAccountConfirmationToken:
    raw: str
    token_hash: str


class AccountConfirmationTokenManager(Protocol):
    def generate(self) -> GeneratedAccountConfirmationToken: ...

    def hash(self, raw_token: str) -> str: ...
