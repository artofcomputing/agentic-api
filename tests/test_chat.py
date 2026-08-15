"""Chat endpoint: happy path and input validation partitions."""


async def test_chat_happy_path_returns_model_output(client, auth_headers):
    response = await client.post(
        "/api/v1/agent/chat",
        json={"user_instruction": "Hello!"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    # With toolsets registered, TestModel deterministically invokes the tool
    # and returns its result, so this also exercises the tool-calling path.
    assert "get_current_time" in body["output"]
    assert body["usage"].get("tool_calls") == 1
    assert (body["usage"].get("total_tokens") or 0) >= 0


async def test_empty_instruction_rejected_by_schema(client, auth_headers):
    response = await client.post(
        "/api/v1/agent/chat",
        json={"user_instruction": ""},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_oversized_instruction_rejected(client, auth_headers):
    response = await client.post(
        "/api/v1/agent/chat",
        # > MAX_INSTRUCTION_CHARS
        json={"user_instruction": "x" * 200_001},
        headers=auth_headers,
    )
    assert response.status_code == 422
