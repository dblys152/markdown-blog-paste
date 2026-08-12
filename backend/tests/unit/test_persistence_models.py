from sqlalchemy import BigInteger

from md2blog.modules.identity.infrastructure.models import UserModel


def test_user_uses_tsid_compatible_primary_key() -> None:
    identifier = UserModel.__table__.c.id

    assert isinstance(identifier.type, BigInteger)
    assert identifier.primary_key
    assert identifier.autoincrement is False


def test_user_email_constraint_has_stable_name() -> None:
    constraint_names = {constraint.name for constraint in UserModel.__table__.constraints}

    assert "uq_users_email" in constraint_names
