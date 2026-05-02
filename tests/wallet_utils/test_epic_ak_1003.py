"""Tests for Epic AK-1003: Staking and rewards."""

import time
from typing import Any

import pytest
import base64
from algokit_utils import AlgoAmount, AlgorandClient
from algokit_utils.transactions.types import OnlineKeyRegistrationParams

from tests.wallet_utils.common import balance, derive_hd_accounts_from_mnemonic


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


def delay(ms: int) -> None:
    """Delay for specified milliseconds."""
    time.sleep(ms / 1000)


def generate_participation_key(algorand: AlgorandClient, address: str) -> dict[str, Any]:
    """Generate participation key for an address using raw HTTP API."""
    algod_client = algorand.client.algod

    # Get current status
    status = algod_client.status()
    current_round = status.last_round

    # Request key generation via raw HTTP
    import httpx
    base_url = algod_client._config.base_url

    # Build URL with path parameter
    url = f"{base_url}/v2/participation/generate/{address}"

    # Make POST request with query params
    response = httpx.post(
        url,
        params={"first": current_round, "last": current_round + 10_000},
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()

    max_iters = 10
    for _ in range(max_iters):
        # Get participation keys via raw HTTP
        keys_url = f"{base_url}/v2/participation"
        keys_response = httpx.get(
            keys_url,
            headers={"Accept": "application/json"},
        )
        keys_response.raise_for_status()
        keys = keys_response.json()

        for key in keys:
            if key["address"] == address and key["key"]["vote-first-valid"] == current_round:
                return {
                    "vote_key": base64.b64decode(key["key"]["vote-participation-key"]),
                    "selection_key": base64.b64decode(key["key"]["selection-participation-key"]),
                    "vote_first": key["key"]["vote-first-valid"],
                    "vote_last": key["key"]["vote-last-valid"],
                    "vote_key_dilution": key["key"]["vote-key-dilution"],
                    "state_proof_key": base64.b64decode(key["key"]["state-proof-key"]),
                }
        delay(1000)

    raise RuntimeError(f"Unable to find part key after {max_iters} seconds")


def go_online(
    algorand: AlgorandClient, address: str, make_eligible: bool
) -> dict:
    """Register an account as online."""
    key = generate_participation_key(algorand, address)

    # Use static fee based on eligibility
    static_fee = AlgoAmount.from_algo(2) if make_eligible else AlgoAmount.from_micro_algo(1000)

    algorand.send.online_key_registration(
        OnlineKeyRegistrationParams(
            sender=address,
            vote_key=key["vote_key"],
            selection_key=key["selection_key"],
            vote_first=key["vote_first"],
            vote_last=key["vote_last"],
            vote_key_dilution=key["vote_key_dilution"],
            state_proof_key=key["state_proof_key"],
            static_fee=static_fee,
        )
    )
    return key


@pytest.mark.skip(reason="Participation key generation requires special LocalNet setup")
class TestEpicAK1003:
    """Epic AK-1003: Staking and rewards."""

    def test_ak_1022_stake_funds(self, algorand: AlgorandClient) -> None:
        """
        AK-1022: Stake funds.
        As a user I want to be able to stake my funds so that I can receive rewards.

        Acceptance Criteria:
        - Given I have setup my wallet
        - And I have a balance over 30K Algo
        - Then I can request a keyreg transaction from a node
        - And I can sign the keyreg transaction

        Note: Exclusion - pooled staking
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=1, algorand=algorand)
        account = accounts[0]

        algorand.account.ensure_funded_from_environment(
            account.addr, AlgoAmount.from_micro_algo(35_000_000_000)
        )
        assert balance(algorand, account) >= 35_000_000_000

        key = go_online(algorand, account.addr, make_eligible=True)
        info = algorand.account.get_information(account.addr)

        # Verify the participation key is registered
        assert info.participation is not None
        assert info.participation.vote_participation_key == key["vote_key"]

    def test_ak_1023_view_rewards(self, algorand: AlgorandClient) -> None:
        """
        AK-1023: View rewards.
        As a user I want to view how much rewards I got and when so that I can accurately report my income.

        Acceptance Criteria:
        - Given I have staked my funds to a node
        - Then I can see how much rewards I'm getting per address
        - And which block I received those rewards

        Return object:
        - when I won the block
        - When I got the payment block
        - reward amount
        - convert block to date:time UTC
        - fees paid
        """
        # This is just the first mainnet block I randomly came across with a proposer payout
        address = "NK2AQRDVHQKRFXD6FBQCPAWPZ433IJU4A3KF5FBY7PTVEVJDCRX2KU7R4Q"
        round_num = 60_449_677

        mainnet = AlgorandClient.mainnet()
        block = mainnet.client.algod.block(round_num)

        header = block.block.header
        if hasattr(header, "proposer"):
            assert str(header.proposer) == address
        else:
            proposer = header.proposer
            assert proposer == address

        if hasattr(header, "proposer_payout"):
            assert header.proposer_payout == 8_694_453
        else:
            payout = header.proposer_payout
            assert payout == 8_694_453

        if hasattr(header, "timestamp"):
            assert header.timestamp == 1_776_778_156
        else:
            ts = header.timestamp
            assert ts == 1_776_778_156

    def test_ak_1024_view_current_amount_staked(self, algorand: AlgorandClient) -> None:
        """
        AK-1024: View current amount staked.
        As a user I want to know how much funds I current have staked so I can calculate the amount of rewards I can expect.

        Acceptance Criteria:
        - Given I have created a wallet
        - And split my funds over addresses
        - And staked my funds
        - Then I can see which addresses are staked
        - Do I have more than 30K algo
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=5, algorand=algorand)
        (
            large_stake_eligible,
            large_stake_ineligible,
            small_stake_eligible,
            offline_addr,
            no_balance,
        ) = accounts

        regular_fee = 0.001
        go_online_fee = 2

        # Fund accounts
        algorand.account.ensure_funded_from_environment(
            large_stake_eligible.addr, AlgoAmount.from_algo(50_000 + go_online_fee)
        )
        algorand.account.ensure_funded_from_environment(
            large_stake_ineligible.addr, AlgoAmount.from_algo(50_000 + regular_fee)
        )
        algorand.account.ensure_funded_from_environment(
            small_stake_eligible.addr, AlgoAmount.from_algo(10_000 + go_online_fee)
        )
        algorand.account.ensure_funded_from_environment(
            offline_addr.addr, AlgoAmount.from_algo(50_000)
        )

        # Register some accounts as online
        go_online(algorand, large_stake_eligible.addr, make_eligible=True)
        go_online(algorand, small_stake_eligible.addr, make_eligible=True)
        go_online(algorand, large_stake_ineligible.addr, make_eligible=False)

        # Check staking statuses
        staking_statuses = []
        for a in accounts:
            info = algorand.account.get_information(a.addr)
            balance_val = info.amount
            online = info.participation is not None

            # incentive_eligible may not exist in the model, handle safely
            try:
                eligible = online and getattr(info, "incentive_eligible", False)
            except (AttributeError, TypeError):
                eligible = False

            enough_stake = online and balance_val > 30_000_000_000  # 30K ALGO in microAlgos

            if online and eligible and enough_stake:
                incentive_status = "earning"
            elif online and not eligible:
                incentive_status = "fee not paid"
            elif online and eligible and not enough_stake:
                incentive_status = "not enough stake"
            else:
                incentive_status = "offline"

            staking_statuses.append(
                {
                    "balance": balance_val,
                    "incentive_status": incentive_status,
                    "address": a.addr,
                }
            )

        # Verify statuses - balance checks are approximate due to fees
        assert staking_statuses[0]["incentive_status"] == "earning"
        assert staking_statuses[1]["incentive_status"] == "fee not paid"
        assert staking_statuses[2]["incentive_status"] == "not enough stake"
        assert staking_statuses[3]["incentive_status"] == "offline"
        assert staking_statuses[4]["incentive_status"] == "offline"
