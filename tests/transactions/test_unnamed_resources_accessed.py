import algosdk
import pytest
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from unittest.mock import MagicMock
from algokit_utils.transactions.transaction_composer import (
    UnnamedResourcesAccessed,
    prepare_group_for_sending,
)


def test_unnamed_resources_deterministic_ordering() -> None:
    raw_resources = {
        "accounts": [
            "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        ],
        "apps": [100, 5, 20],
        "assets": [5000, 10, 300],
        "boxes": [
            {"app": 10, "name": "beta"},
            {"app": 5, "name": "gamma"},
            {"app": 10, "name": "alpha"},
        ],
        "app-locals": [
            {"app": 10, "account": "ZZZ"},
            {"app": 5, "account": "AAA"},
            {"app": 10, "account": "AAA"},
        ],
        "asset-holdings": [
            {"asset": 50, "account": "ZZZ"},
            {"asset": 10, "account": "AAA"},
            {"asset": 50, "account": "AAA"},
        ],
        "extra-box-refs": 3,
    }

    accessed = UnnamedResourcesAccessed(raw_resources)

    # Accounts sorted lexicographically
    assert accessed.accounts == [
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
    ]

    # Apps sorted as integers
    assert accessed.apps == [5, 20, 100]

    # Assets sorted as integers
    assert accessed.assets == [10, 300, 5000]

    # Boxes sorted by string `${app}-${name}`
    assert accessed.boxes == [
        {"app": 10, "name": "alpha"},
        {"app": 10, "name": "beta"},
        {"app": 5, "name": "gamma"},
    ]

    # App-locals sorted by string `${app}-${account}`
    assert accessed.app_locals == [
        {"app": 10, "account": "AAA"},
        {"app": 10, "account": "ZZZ"},
        {"app": 5, "account": "AAA"},
    ]

    # Asset-holdings sorted by string `${asset}-${account}`
    assert accessed.asset_holdings == [
        {"asset": 10, "account": "AAA"},
        {"asset": 50, "account": "AAA"},
        {"asset": 50, "account": "ZZZ"},
    ]

    assert accessed.extra_box_refs == 3


def test_unnamed_resources_empty_and_none() -> None:
    empty_accessed = UnnamedResourcesAccessed({})
    assert empty_accessed.accounts is None
    assert empty_accessed.apps is None
    assert empty_accessed.assets is None
    assert empty_accessed.boxes is None
    assert empty_accessed.app_locals is None
    assert empty_accessed.asset_holdings is None
    assert empty_accessed.extra_box_refs is None

    none_accessed = UnnamedResourcesAccessed(None)
    assert none_accessed.accounts is None


def test_unnamed_resources_invalid_type() -> None:
    with pytest.raises(TypeError, match="Expected dictionary object"):
        UnnamedResourcesAccessed(["invalid"])  # type: ignore[arg-type]


def test_prepare_group_for_sending_deterministic_population() -> None:
    _, sender = algosdk.account.generate_account()
    _, addr1 = algosdk.account.generate_account()
    _, addr2 = algosdk.account.generate_account()
    expected_accounts = sorted([addr1, addr2], key=str)
    reversed_accounts = list(reversed(expected_accounts))

    sp = algosdk.transaction.SuggestedParams(
        fee=1000,
        first=1,
        last=1000,
        gh="wGHE2Pwdvd7S12BL5Fa+pp3LENgQ04ITredAhPBI1cg=",
        gen="testnet-v1.0",
    )
    appl_txn = algosdk.transaction.ApplicationCallTxn(
        sender=sender,
        sp=sp,
        index=1,
        on_complete=algosdk.transaction.OnComplete.NoOpOC,
    )
    atc = AtomicTransactionComposer()
    atc.add_transaction(
        TransactionWithSigner(
            appl_txn, algosdk.atomic_transaction_composer.EmptySigner()
        )
    )

    mock_algod = MagicMock()
    mock_algod.simulate_transactions.return_value = {
        "txn-groups": [
            {
                "failure-message": None,
                "txn-results": [{"txn-result": {}}],
                "unnamed-resources-accessed": {
                    "accounts": reversed_accounts,
                    "apps": [99, 3, 42],
                    "assets": [500, 10],
                },
            }
        ]
    }

    result_atc = prepare_group_for_sending(
        atc, mock_algod, populate_app_call_resources=True
    )
    built_txns = result_atc.build_group()
    populated_appl = built_txns[0].txn
    assert isinstance(populated_appl, algosdk.transaction.ApplicationCallTxn)

    assert populated_appl.accounts == expected_accounts
    assert populated_appl.foreign_apps == [3, 42, 99]
    assert populated_appl.foreign_assets == [10, 500]
