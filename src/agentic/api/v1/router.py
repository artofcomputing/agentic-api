import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from agentic.api.deps import get_fastapi_settings
from agentic.api.security.rate_limit import auth_limiter
from agentic.api.v1.endpoints import agent
from agentic.config.fastapi import FastAPISettings

# auto_error=False: a missing header must yield None (handled below with a
# 401) instead of FastAPI's default 403.
frontend_api_key = APIKeyHeader(
    name="x-api-key", description="API Key", auto_error=False
)


async def verify_api_key(
    request: Request,
    key: str | None = Depends(frontend_api_key),
    s: FastAPISettings = Depends(get_fastapi_settings),
) -> None:
    """Constant-time API-key verification with per-IP failure throttling."""
    client_ip = request.client.host if request.client else "unknown"

    if auth_limiter.is_locked_out(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed authentication attempts; retry later",
            headers={"Retry-After": "300"},
        )

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )
    if key is None:
        auth_limiter.record_failure(client_ip)
        raise unauthorized
    # Compare bytes (header values arrive latin-1 decoded) so non-ASCII input
    # can never raise inside hmac.compare_digest.
    provided = key.encode("latin-1")
    expected = s.api_key.get_secret_value().encode("utf-8")
    if not hmac.compare_digest(provided, expected):
        auth_limiter.record_failure(client_ip)
        raise unauthorized
    auth_limiter.record_success(client_ip)


api_router = APIRouter(dependencies=[Depends(verify_api_key)])

# Register nested endpoints
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
