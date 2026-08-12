from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.main import create_app
from md2blog.shared.infrastructure.database import get_session


@pytest.mark.asyncio
async def test_database_health_check() -> None:
    session = AsyncMock(spec=AsyncSession)

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/database")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    session.execute.assert_awaited_once()
