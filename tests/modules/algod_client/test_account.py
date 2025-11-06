from __future__ import annotations

from algokit_algod_client import AlgodClient, ClientConfig


def test_account_information() -> None:
    """Test account information endpoint using mock server with HAR recording."""
    # Test configuration
    mock_server_url = "http://localhost:8000"
    account_address = "YF6SYO6WNACUF5YDJ6QDY4HNJPIFDP6GZNBDDLDUXFT3C43EDPHMGZVE5U"

    # Expected values
    expected_amount = 328826108369215
    expected_amount_without_pending_rewards = 328826108369215
    expected_min_balance = 100000
    expected_status = "Online"
    expected_last_heartbeat = 54453140
    expected_last_proposed = 57259138
    expected_vote_first_valid = 54437616
    expected_vote_last_valid = 59437616
    expected_vote_key_dilution = 2237
    expected_pending_rewards = 0
    expected_reward_base = 27521
    expected_rewards = 0
    expected_round = 57259141
    expected_total_apps_opted_in = 0
    expected_total_assets_opted_in = 0
    expected_total_created_apps = 0
    expected_total_created_assets = 0

    # Setup client
    config = ClientConfig(
        base_url=mock_server_url,
        token=None,
    )
    algod_client = AlgodClient(config)

    # Make API call
    account = algod_client.account_information(address=account_address)

    # Account Identity
    assert account.address == account_address

    # Account Balance
    assert account.amount == expected_amount
    assert account.amount_without_pending_rewards == expected_amount_without_pending_rewards
    assert account.min_balance == expected_min_balance

    # Account Status
    assert account.status == expected_status

    # Participation Details
    assert account.last_heartbeat == expected_last_heartbeat
    assert account.last_proposed == expected_last_proposed
    assert account.participation is not None
    assert account.participation.vote_first_valid == expected_vote_first_valid
    assert account.participation.vote_last_valid == expected_vote_last_valid
    assert account.participation.vote_key_dilution == expected_vote_key_dilution

    # Rewards
    assert account.pending_rewards == expected_pending_rewards
    assert account.reward_base == expected_reward_base
    assert account.rewards == expected_rewards

    # Round
    assert account.round_ == expected_round

    # Counters (all should be 0 for this account)
    assert account.total_apps_opted_in == expected_total_apps_opted_in
    assert account.total_assets_opted_in == expected_total_assets_opted_in
    assert account.total_created_apps == expected_total_created_apps
    assert account.total_created_assets == expected_total_created_assets

    # Arrays (all should be empty for this account)
    assert account.apps_local_state is None or len(account.apps_local_state) == 0
    assert account.assets is None or len(account.assets) == 0
    assert account.created_apps is None or len(account.created_apps) == 0
    assert account.created_assets is None or len(account.created_assets) == 0
