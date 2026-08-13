from md2blog.settings import Settings


def test_neon_urls_use_the_driver_for_each_workload() -> None:
    settings = Settings(
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
        cors_allowed_origins="http://localhost:5173, https://md2blog.pages.dev",  # type: ignore[arg-type]
    )

    assert settings.cors_allowed_origins == [
        "http://localhost:5173",
        "https://md2blog.pages.dev",
    ]
