from dataclasses import dataclass

from tsidpy import TSID as LibraryTSID


@dataclass(frozen=True, order=True, slots=True)
class TSID:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0 or self.value > (2**63 - 1):
            raise ValueError("TSID must fit in a signed 64-bit integer")

    @classmethod
    def generate(cls) -> "TSID":
        return cls(LibraryTSID.create().number)

    @classmethod
    def from_string(cls, value: str) -> "TSID":
        if not value.isdecimal():
            raise ValueError("TSID string must contain decimal digits only")
        return cls(int(value))

    def __str__(self) -> str:
        return str(self.value)
