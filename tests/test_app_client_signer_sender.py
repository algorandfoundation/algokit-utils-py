import base64
import dataclasses
from typing import Any

import pytest
from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
)
from algosdk import transaction
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner
from algosdk.transaction import GenericSignedTransaction
from algosdk.v2client.algod import AlgodClient


class CustomSigner(TransactionSigner):
    def sign_transactions(
        self, txn_group: list[transaction.Transaction], indexes: list[int]
    ) -> list[GenericSignedTransaction]:
        return []


@dataclasses.dataclass(kw_only=True)
class SignerSender:
    signer: TransactionSigner | None = None
    sender: str | None = None


def use_globals_name(args: Any) -> Any:
    for name, value in globals().items():
        if value == args:
            return name
    return args


fake_key_bytes = b"a" * 64
fake_key = base64.b64encode(fake_key_bytes).decode("utf8")
signer_with_address = AccountTransactionSigner(fake_key)
default_signer = CustomSigner()
override_signer = CustomSigner()
default_sender = "default_sender"
override_sender = "override_sender"
sender_from_signer = address_from_private_key(fake_key)  # type: ignore[no-untyped-call]

no_signer_sender = SignerSender()

default_signer_sender = SignerSender(signer=default_signer, sender=default_sender)
only_default_signer = SignerSender(signer=default_signer)
only_default_sender = SignerSender(sender=default_sender)

override_signer_sender = SignerSender(signer=override_signer, sender=override_sender)
only_override_signer = SignerSender(signer=override_signer)
only_override_sender = SignerSender(sender=override_sender)

default_signer_override_sender = SignerSender(signer=default_signer, sender=override_sender)
override_signer_default_sender = SignerSender(signer=override_signer, sender=default_sender)

only_signer_with_address = SignerSender(signer=signer_with_address)
signer_with_address_default_sender = SignerSender(signer=signer_with_address, sender=default_sender)
signer_with_address_override_sender = SignerSender(signer=signer_with_address, sender=override_sender)
signer_with_address_and_associated_sender = SignerSender(signer=signer_with_address, sender=sender_from_signer)


@pytest.mark.parametrize(
    ("created_with", "called_with", "expected"),
    [
        (default_signer_sender, override_signer_sender, override_signer_sender),
        (default_signer_sender, only_override_sender, default_signer_override_sender),
        (default_signer_sender, only_override_signer, override_signer_default_sender),
        (default_signer_sender, no_signer_sender, default_signer_sender),
        (default_signer_sender, signer_with_address_override_sender, signer_with_address_override_sender),
        (default_signer_sender, only_signer_with_address, signer_with_address_default_sender),
        (signer_with_address_default_sender, override_signer_sender, override_signer_sender),
        (signer_with_address_default_sender, only_override_sender, signer_with_address_override_sender),
        (signer_with_address_default_sender, only_override_signer, override_signer_default_sender),
        (signer_with_address_default_sender, no_signer_sender, signer_with_address_default_sender),
        (
            signer_with_address_default_sender,
            signer_with_address_override_sender,
            signer_with_address_override_sender,
        ),
        (signer_with_address_default_sender, only_signer_with_address, signer_with_address_default_sender),
        (only_default_signer, override_signer_sender, override_signer_sender),
        (only_default_signer, only_override_sender, default_signer_override_sender),
        (only_default_signer, signer_with_address_override_sender, signer_with_address_override_sender),
        (only_default_signer, only_signer_with_address, signer_with_address_and_associated_sender),
        (only_signer_with_address, override_signer_sender, override_signer_sender),
        (only_signer_with_address, only_override_sender, signer_with_address_override_sender),
        (only_signer_with_address, no_signer_sender, signer_with_address_and_associated_sender),
        (only_signer_with_address, signer_with_address_override_sender, signer_with_address_override_sender),
        (only_signer_with_address, only_signer_with_address, signer_with_address_and_associated_sender),
        (only_default_sender, override_signer_sender, override_signer_sender),
        (only_default_sender, only_override_signer, override_signer_default_sender),
        (only_default_sender, signer_with_address_override_sender, signer_with_address_override_sender),
        (only_default_sender, only_signer_with_address, signer_with_address_default_sender),
        (no_signer_sender, override_signer_sender, override_signer_sender),
        (no_signer_sender, signer_with_address_override_sender, signer_with_address_override_sender),
        (no_signer_sender, only_signer_with_address, signer_with_address_and_associated_sender),
    ],
    ids=use_globals_name,
)
def test_resolve_signer_sender(
    algod_client: AlgodClient,
    app_spec: ApplicationSpecification,
    created_with: SignerSender,
    called_with: SignerSender,
    expected: SignerSender,
) -> None:
    app_client = ApplicationClient(algod_client, app_spec, signer=created_with.signer, sender=created_with.sender)

    signer, sender = app_client.resolve_signer_sender(called_with.signer, called_with.sender)

    assert signer == expected.signer
    assert sender == expected.sender


NoSenderError = "No sender provided"
NoSignerError = "No signer provided"


@pytest.mark.parametrize(
    ("created_with", "called_with", "expected"),
    [
        (only_default_signer, only_override_signer, NoSenderError),
        (only_default_signer, no_signer_sender, NoSenderError),
        (only_signer_with_address, only_override_signer, NoSenderError),
        (only_default_sender, only_override_sender, NoSignerError),
        (only_default_sender, no_signer_sender, NoSignerError),
        (no_signer_sender, only_override_sender, NoSignerError),
        (no_signer_sender, only_override_signer, NoSenderError),
        (no_signer_sender, no_signer_sender, NoSignerError),
    ],
    ids=use_globals_name,
)
def test_resolve_signer_sender_failure(
    algod_client: AlgodClient,
    app_spec: ApplicationSpecification,
    created_with: SignerSender,
    called_with: SignerSender,
    expected: str,
) -> None:
    app_client = ApplicationClient(algod_client, app_spec, signer=created_with.signer, sender=created_with.sender)

    with pytest.raises(Exception) as ex:
        app_client.resolve_signer_sender(called_with.signer, called_with.sender)

    assert str(ex.value) == expected
