from collections.abc import Callable

import pytest

from .common import TransactionTestData, load_test_data

TestDataLookup = Callable[[str], TransactionTestData]


@pytest.fixture(scope="module")
def test_data() -> dict[str, TransactionTestData]:
    """Load all test data vectors (mirrors TS testData)."""
    keys = [
        "simplePayment",
        "optInAssetTransfer",
        "simpleAssetTransfer",
        "assetCreate",
        "assetConfig",
        "assetDestroy",
        "assetFreeze",
        "assetUnfreeze",
        "appCall",
        "appCreate",
        "appUpdate",
        "appDelete",
        "onlineKeyRegistration",
        "offlineKeyRegistration",
        "nonParticipationKeyRegistration",
        "heartbeat",
        "stateProof",
        "lsigPayment",
        "msigPayment",
        "msigDelegatedPayment",
        "singleDelegatedPayment",
    ]

    return {key: load_test_data(key) for key in keys}


@pytest.fixture(scope="module")
def test_data_lookup(test_data: dict[str, TransactionTestData]) -> TestDataLookup:
    """Lookup function for test data by key."""
    return test_data.__getitem__
