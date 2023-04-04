import base64
import contextlib
from typing import Any

import pytest
from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
    get_sender_from_signer,
)
from algosdk import transaction
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from algosdk.transaction import GenericSignedTransaction
from algosdk.v2client.algod import AlgodClient


class CustomSigner(TransactionSigner):
    def sign_transactions(
        self, txn_group: list[transaction.Transaction], indexes: list[int]
    ) -> list[GenericSignedTransaction]:
        return []


fake_key = base64.b64encode(b"a" * 64).decode("utf8")


@pytest.mark.parametrize("override_sender", ["override_sender", None])
@pytest.mark.parametrize("override_signer", [CustomSigner(), AccountTransactionSigner(fake_key), None])
@pytest.mark.parametrize("default_sender", ["default_sender", None])
@pytest.mark.parametrize("default_signer", [CustomSigner(), AccountTransactionSigner(fake_key), None])
def test_resolve_signer_sender(
    algod_client: AlgodClient,
    app_spec: ApplicationSpecification,
    default_signer: TransactionSigner | None,
    default_sender: str | None,
    override_signer: TransactionSigner | None,
    override_sender: str | None,
) -> None:
    """Regression test against unexpected changes to signer/sender resolution in ApplicationClient"""
    app_client = ApplicationClient(algod_client, app_spec, signer=default_signer, sender=default_sender)

    expected_signer = override_signer or default_signer
    expected_sender = (
        override_sender
        or get_sender_from_signer(override_signer)
        or default_sender
        or get_sender_from_signer(default_signer)
    )

    ctx: Any
    if expected_signer is None:
        ctx = pytest.raises(ValueError, match="No signer provided")
    elif expected_sender is None:
        ctx = pytest.raises(ValueError, match="No sender provided")
    else:
        ctx = contextlib.nullcontext()

    with ctx:
        signer, sender = app_client.resolve_signer_sender(override_signer, override_sender)

        assert signer == expected_signer
        assert sender == expected_sender
