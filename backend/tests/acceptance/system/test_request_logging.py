import httpx

from md2blog.main import create_app
from md2blog.settings import Settings
from md2blog.shared.infrastructure.logging import REQUEST_ID_HEADER


async def test_response_contains_generated_request_id() -> None:
    app = create_app(Settings())
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert len(response.headers[REQUEST_ID_HEADER]) == 16
