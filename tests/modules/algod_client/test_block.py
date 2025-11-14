import pytest

from algokit_algod_client import AlgodClient, ClientConfig
from algokit_algod_client.models import ParticipationUpdates


@pytest.mark.parametrize(
    ("base_url", "block_rounds"),
    [
        ("https://mainnet-api.4160.nodely.dev", [24098947, 55240407]),
        ("https://testnet-api.4160.nodely.dev", [24099447, 24099347]),
    ],
)
def test_block_endpoint(base_url: str, block_rounds: list[int]) -> None:
    config = ClientConfig(
        base_url=base_url,
        token=None,
    )
    algod_client = AlgodClient(config)

    for block_round in block_rounds:
        resp = algod_client.get_block(round_=block_round, header_only=False)

        assert resp.block.state_proof_tracking is not None
        assert resp.block.transactions is not None
        assert len(resp.block.transactions) > 0

        participation_updates = resp.block.participation_updates
        if participation_updates is not None:
            assert isinstance(participation_updates, ParticipationUpdates)
            if participation_updates.expired_participation_accounts is not None:
                assert isinstance(participation_updates.expired_participation_accounts, list)
            if participation_updates.absent_participation_accounts is not None:
                assert isinstance(participation_updates.absent_participation_accounts, list)
