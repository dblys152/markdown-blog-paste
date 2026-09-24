from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from md2blog.modules.identity.domain.account_confirmation_token import (
    AccountConfirmationToken,
    AccountConfirmationTokenPurpose,
)
from md2blog.modules.identity.infrastructure.account_confirmation_token_repositories import (
    SqlAlchemyAccountConfirmationTokenRepository,
)
from md2blog.shared.domain.tsid import TSID


@pytest.mark.parametrize("purpose", list(AccountConfirmationTokenPurpose))
async def test_lookup_is_scoped_to_token_purpose(purpose: AccountConfirmationTokenPurpose) -> None:
    session = MagicMock()
    session.scalar = AsyncMock(return_value=None)
    repository = SqlAlchemyAccountConfirmationTokenRepository(session, purpose)

    await repository.find_by_token_hash_for_update("hashed-token")

    statement = session.scalar.await_args.args[0]
    sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "account_confirmation_tokens.token_hash = 'hashed-token'" in sql
    assert f"account_confirmation_tokens.purpose = '{purpose.value}'" in sql


async def test_repository_rejects_token_for_other_purpose() -> None:
    repository = SqlAlchemyAccountConfirmationTokenRepository(
        MagicMock(), AccountConfirmationTokenPurpose.EMAIL_VERIFICATION
    )
    now = datetime(2026, 9, 20, tzinfo=UTC)
    token = AccountConfirmationToken(
        id=TSID(1),
        user_id=TSID(2),
        purpose=AccountConfirmationTokenPurpose.PASSWORD_RESET,
        token_hash="hashed-token",
        expires_at=now,
        created_at=now,
    )

    with pytest.raises(ValueError, match="purpose"):
        await repository.add(token)
