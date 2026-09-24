from datetime import timedelta

from md2blog.modules.identity.application.service.email_verification import (
    EmailVerificationPolicy,
)
from md2blog.modules.identity.application.service.password_reset import PasswordResetPolicy
from md2blog.modules.identity.domain.login_failure_state import LoginFailurePolicy
from md2blog.modules.identity.domain.token_policy import ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL
from md2blog.settings import Settings


def test_neon_urls_use_the_driver_for_each_workload() -> None:
    settings = Settings(
        _env_file=None,
        database_url=(
            "postgresql://user:password@ep-example-pooler.neon.tech/neondb"
            "?sslmode=require&channel_binding=require"
        ),
        migration_database_url=(
            "postgresql://user:password@ep-example.neon.tech/neondb"
            "?sslmode=require&channel_binding=require"
        ),
    )

    assert settings.async_database_url.drivername == "postgresql+asyncpg"
    assert settings.async_database_url.query == {"ssl": "require"}
    assert settings.sync_migration_database_url.drivername == "postgresql+psycopg"
    assert settings.sync_migration_database_url.query == {
        "sslmode": "require",
        "channel_binding": "require",
    }


def test_cors_origins_are_parsed_from_comma_separated_environment_value() -> None:
    settings = Settings(
        _env_file=None,
        cors_allowed_origins="http://localhost:5173, https://md2blog.pages.dev",  # type: ignore[arg-type]
    )

    assert settings.cors_allowed_origins == [
        "http://localhost:5173",
        "https://md2blog.pages.dev",
    ]


def test_email_delivery_uses_safe_local_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "MD2Blog API"
    assert settings.smtp_host == "smtp.gmail.com"
    assert settings.smtp_port == 587
    assert settings.smtp_username is None
    assert settings.smtp_password is None
    assert settings.email_from is None
    assert settings.frontend_url == "http://localhost:5173"


def test_auth_policies_have_fixed_defaults() -> None:
    assert EmailVerificationPolicy() == EmailVerificationPolicy(
        token_ttl=timedelta(hours=24),
        resend_cooldown=timedelta(seconds=60),
        daily_limit=5,
    )
    assert PasswordResetPolicy() == PasswordResetPolicy(
        token_ttl=timedelta(minutes=60),
        resend_cooldown=timedelta(seconds=60),
        daily_limit=5,
    )
    assert LoginFailurePolicy() == LoginFailurePolicy(
        failure_limit=10,
        window=timedelta(minutes=10),
        block_duration=timedelta(minutes=5),
    )
    assert ACCESS_TOKEN_TTL == timedelta(minutes=15)
    assert REFRESH_TOKEN_TTL == timedelta(days=14)
