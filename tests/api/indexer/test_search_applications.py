from __future__ import annotations

from base64 import b64decode

import pytest
from indexer_client.client import IndexerClient

from algokit_utils.algorand import AlgorandClient
from algokit_utils.models.account import SigningAccount
from algokit_utils.transactions.transaction_composer import AppCreateParams
from tests.api.indexer.common import fund_account, wait_for_indexer


@pytest.fixture
def funded_account(algorand_localnet: AlgorandClient) -> SigningAccount:
    account = algorand_localnet.account.random()
    fund_account(algorand_localnet, account)
    algorand_localnet.set_signer(sender=account.address, signer=account.signer)
    return account


def test_search_applications_finds_recent_app(
    algorand_localnet: AlgorandClient,
    funded_account: SigningAccount,
    indexer_client: IndexerClient,
) -> None:
    approval_compile = algorand_localnet.client.algod.compile("#pragma version 8\nint 1")  # type: ignore[no-any-unimported]
    clear_compile = algorand_localnet.client.algod.compile("#pragma version 8\nint 1")  # type: ignore[no-any-unimported]
    approval_prog = b64decode(approval_compile["result"])
    clear_prog = b64decode(clear_compile["result"])

    create_result = algorand_localnet.send.app_create(
        AppCreateParams(
            sender=funded_account.address,
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

    wait_for_indexer(indexer_client, tx_id)

    apps = indexer_client.search_for_applications(application_id=app_id)
    assert apps.applications
    assert apps.applications[0].id_ == app_id
