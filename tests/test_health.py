"""Probe contract: unauthenticated, dependency-free, correct status codes."""


async def test_liveness(client):
    response = await client.get("/livez")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


async def test_readiness_after_startup(client):
    response = await client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
