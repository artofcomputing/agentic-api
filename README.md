# Agentic API

A modular, cloud-native API for AI Agents powered by FastAPI, Pydantic, and Pydantic AI.

---

## System Requirements

- **Python**: `>= 3.14`
- **Package Manager**: `uv`
- **Docker**
- **Kubernetes tooling**: `kubectl`, `minikube`

---

## Configuration

All configuration is read from environment variables; `.env.example` is the
authoritative template for the variable schema.

| Scope | Variables | Kubernetes source |
| :--- | :--- | :--- |
| Non-sensitive settings | `FASTAPI_DOCS`, `FASTAPI_HOST`, `AGENT_MODEL`, `AGENT_TOKEN_LIMIT`, `FIBERY_URL`, `LOG_*`, ... | `ConfigMap/agentic-api-config` (`k8s/configmap.yaml`) |
| Secrets | `FASTAPI_API_KEY`, `AGENT_API_KEY`, `FIBERY_API_KEY` | `Secret/agentic-api-secrets` (created at deploy time, never committed) |

For **local development only**, copy `.env.example` to `.env` and fill in the
values. Never commit `.env` or real credentials to version control.

---

## Running Locally (uv)

```bash
uv run python -m agentic.main
```

---

## Running on minikube (Kubernetes)

1. **Start the cluster**:
   ```bash
   minikube start
   ```

2. **Build the image directly inside minikube's runtime** (no registry needed):
   ```bash
   minikube image build -t agentic-api:latest .
   ```
   (Alternative: build with Docker and `minikube image load agentic-api:latest`.)

3. **Create the secrets** — injected into the Pods as environment variables at
   deploy time; never stored in the repository:
   ```bash
   kubectl create secret generic agentic-api-secrets \
     --from-literal=FASTAPI_API_KEY="<your FastAPI key>" \
     --from-literal=AGENT_API_KEY="<your LLM provider API key>" \
     --from-literal=FIBERY_API_KEY="<your Fibery API key>"
   ```

4. **Review `k8s/configmap.yaml`** (at minimum `AGENT_MODEL`, `FIBERY_URL`, and
   `FASTAPI_CORS_ORIGINS`), then deploy the ConfigMap, Deployment, and Service:
   ```bash
   kubectl apply -f k8s/
   ```

5. **Wait for the rollout and verify the Pod is healthy**:
   ```bash
   kubectl rollout status deployment/agentic-api
   kubectl get pods -l app.kubernetes.io/name=agentic-api
   ```

6. **Access the API** (port-forward the ClusterIP Service):
   ```bash
   kubectl port-forward service/agentic-api 8000:80
   ```
   ```bash
   curl http://127.0.0.1:8000/livez                       # liveness probe
   curl http://127.0.0.1:8000/readyz                      # readiness probe
   curl -X POST http://127.0.0.1:8000/api/v1/agent/chat \ # authenticated API
     -H "x-api-key: <FASTAPI_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{"user_instruction": "Hello!"}'
   ```

### Health management

Container health is managed exclusively by Kubernetes probes configured in
`k8s/deployment.yaml`:

| Probe | Endpoint | Purpose |
| :--- | :--- | :--- |
| Startup | `GET /livez` | Allows up to 60s for slow starts before liveness takes over |
| Liveness | `GET /livez` | Restarts the container if the event loop hangs |
| Readiness | `GET /readyz` | Removes the Pod from the Service until startup checks pass |

Both endpoints are unauthenticated and registered outside the `/api/v1` auth
boundary.

### Cleanup

```bash
kubectl delete -f k8s/
kubectl delete secret agentic-api-secrets
minikube stop
```
