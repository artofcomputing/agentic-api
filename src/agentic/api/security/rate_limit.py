"""In-process auth-failure throttling (OWASP API4 mitigation)."""

from collections import OrderedDict
import time


class AuthFailureLimiter:
    """Sliding-window limiter of failed authentication attempts per client IP.

    Single-process only: each Pod keeps its own window. For fleet-wide budgets,
    front the Service with a gateway-level limiter. The tracking table is bounded
    (LRU eviction) so it cannot grow unboundedly itself.
    """

    def __init__(
        self,
        max_failures: int = 5,
        window_seconds: float = 300.0,
        max_tracked: int = 10_000,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.max_tracked = max_tracked
        self._failures: OrderedDict[str, list[float]] = OrderedDict()

    def is_locked_out(self, client_ip: str) -> bool:
        return len(self._prune(client_ip)) >= self.max_failures

    def record_failure(self, client_ip: str) -> None:
        now = time.monotonic()
        attempts = self._prune(client_ip)
        attempts.append(now)
        self._failures[client_ip] = attempts
        while len(self._failures) > self.max_tracked:
            self._failures.popitem(last=False)  # evict oldest entry

    def record_success(self, client_ip: str) -> None:
        self._failures.pop(client_ip, None)

    def _prune(self, client_ip: str) -> list[float]:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        attempts = self._failures.get(client_ip)
        if attempts is None:
            return []
        recent = [t for t in attempts if t > cutoff]
        if recent:
            self._failures[client_ip] = recent
            self._failures.move_to_end(client_ip)
        else:
            self._failures.pop(client_ip, None)
        return recent


auth_limiter = AuthFailureLimiter()
