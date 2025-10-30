from __future__ import annotations

from collections.abc import Callable

import pytest

from .common import TransactionVector, get_test_vector

VectorLookup = Callable[[str], TransactionVector]


@pytest.fixture(scope="module")
def transaction_vectors() -> dict[str, TransactionVector]:
    keys = [
        "simplePayment",
        "optInAssetTransfer",
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
    ]

    return {key: get_test_vector(key) for key in keys}


@pytest.fixture(scope="module")
def vector_lookup(transaction_vectors: dict[str, TransactionVector]) -> VectorLookup:
    return transaction_vectors.__getitem__
