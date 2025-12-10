from base64 import b64decode

import pytest

from algokit_indexer_client import ClientConfig, IndexerClient
from algokit_utils.algorand import AlgorandClient
from algokit_transact.signer import AddressWithSigners
from algokit_utils.transactions.transaction_composer import AppCreateParams
from tests.modules.indexer_client.common import fund_account, wait_for_indexer


@pytest.fixture
def funded_account(algorand_localnet: AlgorandClient) -> AddressWithSigners:
    account = algorand_localnet.account.random()
    fund_account(algorand_localnet, account)
    algorand_localnet.set_signer(sender=account.addr, signer=account.signer)
    return account


@pytest.fixture
def localnet_indexer_client() -> IndexerClient:
    """Create an indexer client connected to localnet."""
    config = ClientConfig(
        base_url="http://localhost:8980",
        token="a" * 64,
    )
    return IndexerClient(config)


@pytest.mark.localnet
def test_search_applications_finds_recent_app(
    algorand_localnet: AlgorandClient,
    funded_account: AddressWithSigners,
    localnet_indexer_client: IndexerClient,
) -> None:
    """Test searching for applications using localnet indexer.

    NOTE: This test requires localnet to be running with indexer.
    """
    approval_compile = algorand_localnet.client.algod.teal_compile(b"#pragma version 8\nint 1", sourcemap=False)
    clear_compile = algorand_localnet.client.algod.teal_compile(b"#pragma version 8\nint 1", sourcemap=False)
    approval_prog = b64decode(approval_compile.result)
    clear_prog = b64decode(clear_compile.result)

    create_result = algorand_localnet.send.app_create(
        AppCreateParams(
            sender=funded_account.addr,
            approval_program=approval_prog,
            clear_state_program=clear_prog,
            schema={
                "global_ints": 0,
                "global_byte_slices": 0,
                "local_ints": 0,
                "local_byte_slices": 0,
            },
        )
    )

    app_id = create_result.app_id
    tx_id = create_result.tx_id
    assert app_id
    assert tx_id

    wait_for_indexer(localnet_indexer_client, tx_id)

    apps = localnet_indexer_client.search_for_applications(application_id=app_id)
    assert apps.applications
    assert apps.applications[0].id_ == app_id
