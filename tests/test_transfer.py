from algokit_utils import ABICreateCallArgs, Account, ApplicationClient, TransferParameters, transfer


def test_transfer(client_fixture: ApplicationClient, creator: Account) -> None:
    client_fixture.deploy(
        "v1",
        create_args=ABICreateCallArgs(
            method="create",
        ),
    )

    requested_amount = 100_000
    transfer(
        TransferParameters(from_account=creator, to_address=client_fixture.app_address, amount=requested_amount),
        client_fixture.algod_client,
    )

    account_info = client_fixture.algod_client.account_info(client_fixture.app_address)
    assert isinstance(account_info, dict)
    actual_amount = account_info.get("amount")
    assert actual_amount == requested_amount
