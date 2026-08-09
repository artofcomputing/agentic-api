import hmac

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from agentic.api.deps import get_fastapi_settings
from agentic.api.v1.endpoints import agent
from agentic.config.fastapi import FastAPISettings

frontend_api_key = APIKeyHeader(name="x-api-key", description="API Key")


async def verify_api_key(
    key: str = Depends(frontend_api_key),
    s: FastAPISettings = Depends(get_fastapi_settings),
) -> None:
    if not hmac.compare_digest(key, s.api_key.get_secret_value()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


api_router = APIRouter(dependencies=[Depends(verify_api_key)])

# Register nested endpoints
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
