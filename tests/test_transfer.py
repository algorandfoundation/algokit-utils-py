from algokit_utils import ABICallArgs, Account, ApplicationClient, TransferParameters, transfer


def test_transfer(client_fixture: ApplicationClient, creator: Account) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICallArgs(
            method="create",
        ),
    )

    requested_amount = 100_000
    transfer(
        TransferParameters(from_account=creator, to_address=client_fixture.app_address, amount=requested_amount),
        client_fixture.algod_client,
    )

    actual_amount = client_fixture.algod_client.account_info(client_fixture.app_address).get("amount")
    assert actual_amount == requested_amount
