import httpx
import pytest

from algokit_algod_client import AlgodClient, ClientConfig
from algokit_utils.algorand import AlgorandClient


@pytest.mark.localnet
def test_get_suggested_params() -> None:
    """Test suggested params using localnet."""
    algod_client = AlgorandClient.default_localnet().client.algod
    params = algod_client.suggested_params()
    assert isinstance(params.genesis_id, str)
    assert params.genesis_id
    assert isinstance(params.min_fee, int)
    assert params.min_fee > 0


def test_suggested_params_error_handling() -> None:
    """Test error handling for invalid host."""
    bad = AlgodClient(ClientConfig(base_url="http://invalid-host:4001", token="a" * 64))
    with pytest.raises(httpx.HTTPError):
        bad.suggested_params()
