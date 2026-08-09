"""Unauthenticated probe endpoints for container orchestration.

Kubernetes Startup/Liveness/Readiness probes hit these routes. They are
registered at the application root, OUTSIDE the authenticated ``/api/v1``
boundary, so orchestrators never need API credentials and probe traffic is
unaffected by secret rotation.

* ``/livez``  -- Liveness: is the process (event loop) still responsive?
* ``/readyz`` -- Readiness: has startup completed, can we serve traffic?

The deprecated single ``/healthz`` convention is intentionally avoided in
favor of split liveness/readiness endpoints, mirroring the Kubernetes API
server's own ``/livez`` and ``/readyz`` routes.
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

    Returns ``503`` until the application lifespan fail-fast checks have
    completed (``app.state.ready``). Kubernetes removes the Pod from the
    Service endpoints while this probe fails, without restarting it.
    """
    if not getattr(request.app.state, "ready", False):
        logger.debug("Readiness probe failed: application not ready")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application is not ready to serve traffic.",
        )
    return {"status": "ready"}
