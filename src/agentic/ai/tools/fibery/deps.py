from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import SecretStr

if TYPE_CHECKING:
    from agentic.ai.tools.fibery.graphql_client import Client


@dataclass(frozen=True)
class FiberyDeps:
    """Dependency container for Fibery-related client connections.

    Frozen so instances are immutable and safely shareable, and the API key is
    held as a ``SecretStr`` so it cannot leak through ``repr()``, debugger
    dumps, or exception messages. The key is unwrapped only inside
    ``headers``, at the last hop before the network call.
    """

    url: str
    api_key: SecretStr

    @property
    def headers(self) -> dict[str, str]:
        """Dynamically builds the authorization headers required for Fibery."""
        return {
            "Authorization": f"Token {self.api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[Client]:
        """Lazily initializes the GraphQL Client only when requested by a tool."""
        from agentic.ai.tools.fibery.graphql_client import Client

        async with Client(url=self.url, headers=self.headers) as client:
            yield client
