import pytest

from md2blog.shared.domain.tsid import TSID


def test_generated_tsid_fits_in_postgresql_bigint() -> None:
    identifier = TSID.generate()

    assert 0 <= identifier.value <= (2**63 - 1)
    assert TSID.from_string(str(identifier)) == identifier


@pytest.mark.parametrize("value", ["", "-1", "12.3", "not-an-id"])
def test_tsid_rejects_non_decimal_strings(value: str) -> None:
    with pytest.raises(ValueError):
        TSID.from_string(value)


def test_tsid_rejects_values_outside_signed_bigint() -> None:
    with pytest.raises(ValueError):
        TSID(2**63)
