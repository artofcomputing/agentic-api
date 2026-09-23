"""Request hardening middleware."""

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestBodyLimitMiddleware:
    """Reject HTTP request bodies larger than ``max_body_bytes`` with 413.

    Enforces both the declared Content-Length header (fast reject) and the
    actual streamed size, so chunked transfers cannot bypass the cap.
    """

    def __init__(self, app: ASGIApp, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        declared = headers.get(b"content-length")
        if declared is not None and int(declared) > self.max_body_bytes:
            await self._send_413(send)
            return

        received = 0

        async def guarded_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body") or b"")
                if received > self.max_body_bytes:
                    await self._send_413(send)
                    raise _BodyLimitExceeded
            return message

        try:
            await self.app(scope, guarded_receive, send)
        except _BodyLimitExceeded:
            pass  # 413 already emitted

    @staticmethod
    async def _send_413(send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"connection", b"close"),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b'{"detail":"Request body too large"}',
            }
        )


class _BodyLimitExceeded(Exception):
    """Internal control-flow signal; never escapes the middleware."""
