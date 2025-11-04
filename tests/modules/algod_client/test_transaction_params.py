from __future__ import annotations

import httpx
import pytest

from algokit_algod_client import AlgodClient, ClientConfig


def test_get_transaction_params(algod_client: AlgodClient) -> None:
    params = algod_client.transaction_params()
    assert isinstance(params.genesis_id, str)
    assert params.genesis_id
    assert isinstance(params.min_fee, int)
    assert params.min_fee > 0


def test_transaction_params_error_handling() -> None:
    # Invalid host should fail
    bad = AlgodClient(ClientConfig(base_url="http://invalid-host:4001", token="a" * 64))
    with pytest.raises(httpx.HTTPError):
        bad.transaction_params()
