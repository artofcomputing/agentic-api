"""Auth boundary: /api/v1 requires a valid x-api-key; probes do not."""


async def test_chat_without_api_key_returns_401(client):
    response = await client.post(
        "/api/v1/agent/chat", json={"user_instruction": "Hello!"}
    )
    assert response.status_code == 401


async def test_chat_with_wrong_api_key_returns_401(client):
    response = await client.post(
        "/api/v1/agent/chat",
        json={"user_instruction": "Hello!"},
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code == 401


async def test_probes_are_unauthenticated(client):
    assert (await client.get("/livez")).status_code == 200
    assert (await client.get("/readyz")).status_code == 200
