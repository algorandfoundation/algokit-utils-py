from algokit_utils import ABICallArgs, Account, ApplicationClient, TransferParameters, transfer


def test_transfer(client_fixture: ApplicationClient, creator: Account) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICallArgs(
            method="create",
        ),
    )

    payment, txn = transfer(
        TransferParameters(from_account=creator, to_address=client_fixture.app_address, amount=100_000),
        client_fixture.algod_client,
    )

    assert txn != ""
