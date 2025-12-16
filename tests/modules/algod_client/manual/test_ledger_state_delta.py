import pytest

from algokit_algod_client import AlgodClient, ClientConfig
from algokit_algod_client.models import LedgerStateDelta


@pytest.mark.parametrize(
    ("base_url", "block_rounds"),
    [
        ("https://mainnet-api.4160.nodely.dev", [24098947, 55240407]),
        ("https://testnet-api.4160.nodely.dev", [24099447, 24099347]),
    ],
)
def test_ledger_state_delta_endpoint(base_url: str, block_rounds: list[int]) -> None:
    config = ClientConfig(
        base_url=base_url,
        token=None,
    )
    algod_client = AlgodClient(config)

    for block_round in block_rounds:
        raw_delta = algod_client.get_ledger_state_delta(round_=block_round)

        assert isinstance(raw_delta, LedgerStateDelta)
        assert raw_delta.accounts is not None
        assert raw_delta.block.header.txn_commitments.transactions_root_sha256 is not None
