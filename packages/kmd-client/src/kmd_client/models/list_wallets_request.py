from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ListWalletsRequest:
    """
    APIV1GETWalletsRequest is the request for `GET /v1/wallets`
    """
