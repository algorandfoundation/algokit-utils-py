from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class VersionsRequest:
    """
    VersionsRequest is the request for `GET /versions`
    """
