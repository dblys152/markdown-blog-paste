import httpx

from md2blog.main import create_app
from md2blog.settings import Settings

ALLOWED_ORIGIN = "https://md2blog.pages.dev"


async def test_preflight_allows_configured_origin_with_credentials() -> None:
    app = create_app(Settings(cors_allowed_origins=[ALLOWED_ORIGIN]))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/auth/refresh",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"


async def test_preflight_does_not_allow_unconfigured_origin() -> None:
    app = create_app(Settings(cors_allowed_origins=[ALLOWED_ORIGIN]))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/auth/refresh",
            headers={
                "Origin": "https://malicious.example",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
