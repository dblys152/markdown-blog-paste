from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not normalized:
            raise ValueError("email must not be empty")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RawPassword:
    value: str


@dataclass(frozen=True, slots=True)
class PasswordHash:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("password hash must not be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class DisplayName:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("display name must not be empty")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
