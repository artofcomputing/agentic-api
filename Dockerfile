# --- Stage 1: Build Dependencies ---
FROM python:3.14-slim AS builder

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install system dependencies needed for compiling C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Environment settings for uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT="/opt/venv"

# 1. Cache dependencies (installs dependencies into /opt/venv without project source)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2. Install application package as NON-EDITABLE into /opt/venv
COPY README.md ./
COPY src/ src/
RUN uv sync --frozen --no-dev --no-editable

# --- Stage 2: Final Production Run Image ---
FROM python:3.14-slim AS runner

LABEL org.opencontainers.image.title="agentic-api" \
      org.opencontainers.image.description="A modular, cloud-native API for AI Agents powered by FastAPI, Pydantic, and Pydantic AI" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.source="https://github.com/artofcomputing/agentic-api"

WORKDIR /app

# Create a non-root user for security. Numeric UID/GID are pinned so
# Kubernetes can enforce runAsNonRoot against a verifiable user ID.
RUN groupadd -r -g 1000 appgroup && useradd -r -u 1000 -g appgroup -s /sbin/nologin appuser

# Copy virtual environment containing all pre-built runtime dependencies AND application code
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Ensure runtime directories are owned by the non-root user
RUN chown -R appuser:appgroup /app

# Use the non-root user to run the container
USER appuser

# Documentation only: the Service targetPort and probes use this port.
EXPOSE 8000

# NOTE: No HEALTHCHECK instruction on purpose. This project runs under
# Kubernetes, which ignores Docker HEALTHCHECK; container health is managed by
# the Deployment's Startup/Liveness/Readiness probes against the
# unauthenticated /livez and /readyz endpoints (see k8s/deployment.yaml).

# Start the app via the installed package entrypoint
ENTRYPOINT ["python", "-m", "agentic.main"]