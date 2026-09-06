from sqlalchemy import BigInteger

from md2blog.modules.identity.infrastructure.models import (
    EmailVerificationTokenModel,
    PasswordResetTokenModel,
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


def test_email_verification_token_has_stable_constraints_and_indexes() -> None:
    table = EmailVerificationTokenModel.__table__

    assert "uq_email_verification_tokens_token_hash" in {
        constraint.name for constraint in table.constraints
    }
    assert "ix_email_verification_tokens_user_id" in {index.name for index in table.indexes}


def test_password_reset_token_has_stable_constraints_and_indexes() -> None:
    table = PasswordResetTokenModel.__table__

    assert "uq_password_reset_tokens_token_hash" in {
        constraint.name for constraint in table.constraints
    }
    assert "ix_password_reset_tokens_user_id" in {index.name for index in table.indexes}
    foreign_key = next(iter(table.c.user_id.foreign_keys))
    assert foreign_key.ondelete == "CASCADE"
