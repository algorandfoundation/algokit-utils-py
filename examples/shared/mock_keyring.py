# ruff: noqa: S105, S106
"""
Mock keyring implementation for CI/testing environments.

This module provides a mock keyring that stores secrets in memory using a
dictionary. It's automatically used when running in GitHub Actions CI to
avoid issues with OS keyring availability.

WARNING: This is not secure and should only be used for testing.
"""

from __future__ import annotations

import os
from typing import ClassVar, Protocol


class KeyringProtocol(Protocol):
    """Protocol defining the interface for keyring implementations."""

    def get_password(self, service: str, username: str) -> str | None: ...
    def set_password(self, service: str, username: str, password: str) -> None: ...


class MockKeyring:
    """In-memory keyring for CI/testing when OS keyring is unavailable.

    WARNING: This is not secure and should only be used for testing.
    Secrets are stored in a static dictionary and persist for the lifetime
    of the process.
    """

    _storage: ClassVar[dict[str, dict[str, str]]] = {}

    def get_password(self, service: str, username: str) -> str | None:
        """Retrieve a password from the mock storage."""
        return self._storage.get(service, {}).get(username)

    def set_password(self, service: str, username: str, password: str) -> None:
        """Store a password in the mock storage."""
        if service not in self._storage:
            self._storage[service] = {}
        self._storage[service][username] = password


class RealKeyringWrapper:
    """Wrapper for the real keyring module to implement KeyringProtocol."""

    def __init__(self) -> None:
        import keyring

        self._keyring = keyring

    def get_password(self, service: str, username: str) -> str | None:
        """Retrieve a password using the real keyring."""
        return self._keyring.get_password(service, username)

    def set_password(self, service: str, username: str, password: str) -> None:
        """Store a password using the real keyring."""
        self._keyring.set_password(service, username, password)


def get_keyring() -> KeyringProtocol:
    """Get the appropriate keyring implementation.

    Returns an instance that implements KeyringProtocol.
    Uses MockKeyring when running in GitHub Actions, otherwise
    uses the real OS keyring via RealKeyringWrapper.

    Returns:
        A KeyringProtocol instance (either MockKeyring or RealKeyringWrapper)
    """
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return MockKeyring()

    return RealKeyringWrapper()
