import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_get_workflows_empty(client: AsyncClient):
    # Depending on if DB has data, this might verify structure
    response = await client.get("/api/v1/workflows")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_geo_analytics(client: AsyncClient):
    response = await client.get("/api/v1/analytics/geographic-divergence")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "divergence_score" in data[0]
