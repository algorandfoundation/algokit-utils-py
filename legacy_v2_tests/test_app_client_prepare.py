import base64
from typing import TYPE_CHECKING

from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
)
from algosdk.atomic_transaction_composer import AccountTransactionSigner

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient


def test_app_client_prepare_with_no_existing_or_new(
    algod_client: "AlgodClient", app_spec: ApplicationSpecification
) -> None:
    client = ApplicationClient(algod_client, app_spec)

    new_client = client.prepare()
    assert new_client.signer is None
    assert new_client.sender is None


def test_app_client_prepare_with_existing_signer_sender(
    algod_client: "AlgodClient", app_spec: ApplicationSpecification
) -> None:
    signer = AccountTransactionSigner(base64.b64encode(b"a" * 64).decode("utf-8"))
    client = ApplicationClient(algod_client, app_spec, signer=signer, sender="a sender")

    new_client = client.prepare()
    assert isinstance(new_client.signer, AccountTransactionSigner)
    assert signer.private_key == new_client.signer.private_key
    assert client.sender == new_client.sender


def test_app_client_prepare_with_new_sender(algod_client: "AlgodClient", app_spec: ApplicationSpecification) -> None:
    client = ApplicationClient(algod_client, app_spec)

    new_client = client.prepare(sender="new_sender")
    assert new_client.sender == "new_sender"


def test_app_client_prepare_with_new_signer(algod_client: "AlgodClient", app_spec: ApplicationSpecification) -> None:
    signer = AccountTransactionSigner(base64.b64encode(b"a" * 64).decode("utf-8"))
    client = ApplicationClient(algod_client, app_spec)

    new_client = client.prepare(signer=signer)
    assert isinstance(new_client.signer, AccountTransactionSigner)
    assert new_client.signer.private_key == signer.private_key
