"""Unauthenticated probe endpoints for container orchestration.

Kubernetes Startup/Liveness/Readiness probes hit these routes. They are
registered at the application root, OUTSIDE the authenticated ``/api/v1``
boundary, so orchestrators never need API credentials and probe traffic is
unaffected by secret rotation.

* ``/livez``  -- Liveness
* ``/readyz`` -- Readiness
"""

import logging

from fastapi import APIRouter, HTTPException, Request, status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Probes"])


@router.get(
    "/livez",
    summary="Liveness probe",
    response_model=dict[str, str],
)
async def liveness() -> dict[str, str]:
    """Liveness probe target.

    Kept dependency-free on purpose: reaching this handler proves the event
    loop is responsive. Kubernetes restarts the container when this probe
    keeps failing (e.g. a deadlocked event loop times out the HTTP request).
    """
    return {"status": "alive"}


@router.get(
    "/readyz",
    summary="Readiness probe",
    response_model=dict[str, str],
)
async def readiness(request: Request) -> dict[str, str]:
    """Readiness probe target.

    ready is True after the lifespan fail-fast checks pass
    (prompt readable + LLM model constructible). It deliberately does NOT
    verify upstream LLM provider reachability: transient provider flaps must
    not remove healthy Pods from the Service. Provider failures are handled
    by the error-mapping layer (agent endpoint -> 502/503).
    """
    if not getattr(request.app.state, "ready", False):
        logger.debug("Readiness probe failed: application not ready")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application is not ready to serve traffic.",
        )
    return {"status": "ready"}
