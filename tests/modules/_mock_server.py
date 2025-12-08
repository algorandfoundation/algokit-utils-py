"""Mock server infrastructure for algod/indexer/kmd client testing.

This module provides connectivity to externally-managed mock servers that replay
pre-recorded HAR files for deterministic API testing. Only used by algod_client,
indexer_client, and kmd_client test modules.

The mock server lifecycle is managed externally:
    - CI: Started via GitHub Action (see .github/workflows/)
    - Local development: Started manually via bun (see algokit-polytest repo)

Tests connect to the mock server via environment variables specifying the server URLs.

Environment Variables:
    MOCK_ALGOD_URL: External algod mock server URL (e.g., http://localhost:8000)
    MOCK_INDEXER_URL: External indexer mock server URL (e.g., http://localhost:8002)
    MOCK_KMD_URL: External KMD mock server URL (e.g., http://localhost:8001)

For mock server setup instructions, see:
    https://github.com/algorandfoundation/algokit-polytest
"""

from __future__ import annotations

import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

# Environment variable names for external server URLs
EXTERNAL_URL_ENV_VARS = {
    "algod": "MOCK_ALGOD_URL",
    "indexer": "MOCK_INDEXER_URL",
    "kmd": "MOCK_KMD_URL",
}

DEFAULT_TOKEN = "a" * 64


@dataclass
class MockServer:
    """Connection info for an externally-managed mock server.

    The server lifecycle is managed externally (GitHub Action or manual bun process),
    so this class only holds connection information.

    Attributes:
        base_url: The base URL of the mock server (e.g., http://localhost:8000)
        client_type: The type of client this server mocks (algod, indexer, or kmd)
    """

    base_url: str
    client_type: str

    def stop(self) -> None:
        """No-op: Server lifecycle is managed externally."""
        pass


def _check_server_health(url: str, timeout: float = 5.0) -> bool:
    """Check if the mock server is reachable and responding.

    The mock server uses Fastify with a catch-all route, so any request
    should work. We use the /health path by convention, but any path would
    respond (possibly with a 404/500 from HAR replay, which still indicates readiness).

    Args:
        url: Base URL of the server to check
        timeout: Maximum time to wait for health check (seconds)

    Returns:
        True if server is healthy, False otherwise
    """
    import time

    health_url = f"{url.rstrip('/')}/health"
    start = time.time()

    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(health_url, method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except urllib.error.HTTPError:
            # HTTP error responses (4xx, 5xx) still indicate server is ready
            return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.2)

    return False


def get_mock_server(client_type: str) -> MockServer:
    """Get connection to an externally-managed mock server.

    Reads the appropriate environment variable for the server URL,
    validates the server is reachable, and returns connection info.

    Args:
        client_type: Type of mock server to connect to (algod, indexer, or kmd)

    Returns:
        MockServer instance with connection info

    Raises:
        ValueError: If client_type is not recognized
        RuntimeError: If environment variable is not set or server is not reachable
    """
    if client_type not in EXTERNAL_URL_ENV_VARS:
        raise ValueError(
            f"Unknown client_type: {client_type}. Must be one of: {', '.join(EXTERNAL_URL_ENV_VARS.keys())}"
        )

    env_var = EXTERNAL_URL_ENV_VARS[client_type]
    server_url = os.environ.get(env_var)

    if not server_url:
        raise RuntimeError(
            f"Environment variable {env_var} is not set. "
            f"The mock server must be started externally before running tests. "
            f"For local development, run the mock server via bun. "
            f"See https://github.com/algorandfoundation/algokit-polytest for setup instructions."
        )

    if not _check_server_health(server_url):
        raise RuntimeError(
            f"Mock server at {server_url} (from {env_var}) is not reachable. "
            f"Ensure the mock server is running and accessible. "
            f"For local development, run the mock server via bun. "
            f"See https://github.com/algorandfoundation/algokit-polytest for setup instructions."
        )

    return MockServer(base_url=server_url.rstrip("/"), client_type=client_type)
