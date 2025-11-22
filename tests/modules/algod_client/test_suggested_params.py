import httpx
import pytest

from algokit_algod_client import AlgodClient, ClientConfig


def test_get_suggested_params(algod_client: AlgodClient) -> None:
    params = algod_client.suggested_params()
    assert isinstance(params.genesis_id, str)
    assert params.genesis_id
    assert isinstance(params.min_fee, int)
    assert params.min_fee > 0


def test_suggested_params_error_handling() -> None:
    # Invalid host should fail
    bad = AlgodClient(ClientConfig(base_url="http://invalid-host:4001", token="a" * 64))
    with pytest.raises(httpx.HTTPError):
        bad.suggested_params()
