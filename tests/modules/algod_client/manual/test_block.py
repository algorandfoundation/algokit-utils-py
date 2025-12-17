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
        resp = algod_client.block(round_=block_round, header_only=False)

        assert resp.block.header.state_proof_tracking is not None
        assert resp.block.payset is not None
        assert len(resp.block.payset) > 0

        participation_updates = resp.block.header.participation_updates
        if participation_updates is not None:
            assert isinstance(participation_updates, ParticipationUpdates)
            if participation_updates.expired_participation_accounts is not None:
                assert isinstance(participation_updates.expired_participation_accounts, tuple)
            if participation_updates.absent_participation_accounts is not None:
                assert isinstance(participation_updates.absent_participation_accounts, tuple)


@pytest.mark.parametrize(
    ("base_url", "block_round"),
    [
        # Block 56492866 is an empty block (no transactions) with new protocol format
        # (uses txn256/txn512 instead of txn)
        ("https://mainnet-api.4160.nodely.dev", 56492866),
    ],
)
def test_block_endpoint_empty_block(base_url: str, block_round: int) -> None:
    """Test parsing of empty blocks (no transactions) with newer protocol format."""
    config = ClientConfig(
        base_url=base_url,
        token=None,
    )
    algod_client = AlgodClient(config)

    resp = algod_client.block(round_=block_round, header_only=False)

    # Verify block header is parsed correctly
    assert resp.block.header.round == block_round
    assert resp.block.header.state_proof_tracking is not None

    # This block uses newer protocol format with txn256/txn512 instead of txn
    # txn is missing from wire, defaults to 32 zero bytes
    assert resp.block.header.txn_commitments.transactions_root == bytes(32)
    # txn256 has actual value (not zeros)
    assert resp.block.header.txn_commitments.transactions_root_sha256 is not None
    assert resp.block.header.txn_commitments.transactions_root_sha256 != bytes(32)
    assert len(resp.block.header.txn_commitments.transactions_root_sha256) == 32
    # txn512 has actual value (64 bytes)
    assert resp.block.header.transactions_root_sha512 is not None
    assert resp.block.header.transactions_root_sha512 != bytes(64)
    assert len(resp.block.header.transactions_root_sha512) == 64

    # Empty block has no transactions
    assert resp.block.payset is None
