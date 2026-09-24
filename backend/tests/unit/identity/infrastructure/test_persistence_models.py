from sqlalchemy import BigInteger

from md2blog.modules.identity.infrastructure.models import (
    AccountConfirmationTokenModel,
    LoginFailureStateModel,
    UserModel,
)


def test_user_uses_tsid_compatible_primary_key() -> None:
    identifier = UserModel.__table__.c.id

    assert isinstance(identifier.type, BigInteger)
    assert identifier.primary_key
    assert identifier.autoincrement is False


def test_user_email_constraint_has_stable_name() -> None:
    constraint_names = {constraint.name for constraint in UserModel.__table__.constraints}

    assert "uq_users_email" in constraint_names


def test_account_confirmation_token_has_stable_constraints_and_indexes() -> None:
    table = AccountConfirmationTokenModel.__table__

    assert "uq_account_confirmation_tokens_token_hash" in {
        constraint.name for constraint in table.constraints
    }
    assert "ck_account_confirmation_tokens_purpose" in {
        constraint.name for constraint in table.constraints
    }
    assert "ix_account_confirmation_tokens_user_id" in {index.name for index in table.indexes}
    assert "ix_account_confirmation_tokens_purpose" in {index.name for index in table.indexes}
    foreign_key = next(iter(table.c.user_id.foreign_keys))
    assert foreign_key.ondelete == "CASCADE"


def test_login_failure_state_belongs_to_user() -> None:
    table = LoginFailureStateModel.__table__

    assert [column.name for column in table.primary_key.columns] == [
        "user_id",
    ]
    assert next(iter(table.c.user_id.foreign_keys)).ondelete == "CASCADE"
