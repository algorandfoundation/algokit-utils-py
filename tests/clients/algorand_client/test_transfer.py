import httpx
import pytest
from pytest_httpx._httpx_mock import HTTPXMock

from algokit_utils.algorand import AlgorandClient
from algokit_utils.clients.dispenser_api_client import DispenserApiConfig, TestNetDispenserApiClient
from algokit_utils.models.account import SigningAccount
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import (
    AssetOptInParams,
    AssetTransferParams,
    PaymentParams,
)
from tests.conftest import generate_test_asset


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> SigningAccount:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(
        new_account, dispenser, AlgoAmount.from_algo(100), min_funding_increment=AlgoAmount.from_algo(1)
    )
    algorand.set_signer(sender=new_account.address, signer=new_account.signer)
    return new_account


def test_transfer_algo_is_sent_and_waited_for(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    second_account = algorand.account.random()

    result = algorand.send.payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=second_account.address,
            amount=AlgoAmount.from_algo(5),
            note=b"Transfer 5 Algos",
        )
    )

    account_info = algorand.account.get_information(second_account)

    assert result.transaction.payment
    assert result.transaction.payment.amt == 5_000_000

    assert result.transaction.payment.sender == funded_account.address == result.confirmation["txn"]["txn"]["snd"]  # type: ignore  # noqa: PGH003
    assert account_info.amount == 5_000_000


def test_transfer_algo_respects_string_lease(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    second_account = algorand.account.random()

    algorand.send.payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=second_account.address,
            amount=AlgoAmount.from_algo(1),
            lease=b"test",
        )
    )

    with pytest.raises(Exception, match="overlapping lease"):
        algorand.send.payment(
            PaymentParams(
                sender=funded_account.address,
                receiver=second_account.address,
                amount=AlgoAmount.from_algo(2),
                lease=b"test",
            )
        )


def test_transfer_algo_respects_byte_array_lease(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    second_account = algorand.account.random()

    algorand.send.payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=second_account.address,
            amount=AlgoAmount.from_algo(1),
            lease=b"\x01\x02\x03\x04",
        )
    )

    with pytest.raises(Exception, match="overlapping lease"):
        algorand.send.payment(
            PaymentParams(
                sender=funded_account.address,
                receiver=second_account.address,
                amount=AlgoAmount.from_algo(2),
                lease=b"\x01\x02\x03\x04",
            )
        )


def test_transfer_asa_respects_lease(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    test_asset_id = generate_test_asset(algorand, funded_account, 100)

    second_account = algorand.account.random()
    algorand.account.ensure_funded(
        account_to_fund=second_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    algorand.send.asset_opt_in(
        AssetOptInParams(
            sender=second_account.address,
            asset_id=test_asset_id,
        )
    )

    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=funded_account.address,
            receiver=second_account.address,
            asset_id=test_asset_id,
            amount=1,
            lease=b"test",
        )
    )

    with pytest.raises(Exception, match="overlapping lease"):
        algorand.send.asset_transfer(
            AssetTransferParams(
                sender=funded_account.address,
                receiver=second_account.address,
                asset_id=test_asset_id,
                amount=2,
                lease=b"test",
            )
        )


def test_transfer_asa_receiver_not_opted_in(
    algorand: AlgorandClient,
    funded_account: SigningAccount,
) -> None:
    test_asset_id = generate_test_asset(algorand, funded_account, 100)
    second_account = algorand.account.random()

    with pytest.raises(Exception, match="receiver error: must optin"):
        algorand.send.asset_transfer(
            AssetTransferParams(
                sender=funded_account.address,
                receiver=second_account.address,
                asset_id=test_asset_id,
                amount=1,
                note=b"Transfer 5 assets with id %d" % test_asset_id,
            )
        )


def test_transfer_asa_sender_not_opted_in(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    test_asset_id = generate_test_asset(algorand, funded_account, 100)
    second_account = algorand.account.random()
    algorand.account.ensure_funded(
        account_to_fund=second_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    with pytest.raises(Exception, match=f"asset {test_asset_id} missing from {second_account.address}"):
        algorand.send.asset_transfer(
            AssetTransferParams(
                sender=second_account.address,
                receiver=funded_account.address,
                asset_id=test_asset_id,
                amount=1,
                note=b"Transfer 5 assets with id %d" % test_asset_id,
            )
        )


def test_transfer_asa_asset_doesnt_exist(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    second_account = algorand.account.random()
    algorand.account.ensure_funded(
        account_to_fund=second_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    with pytest.raises(Exception, match=f"asset 123123 missing from {funded_account.address}"):
        algorand.send.asset_transfer(
            AssetTransferParams(
                sender=funded_account.address,
                receiver=second_account.address,
                asset_id=123123,
                amount=5,
                note=b"Transfer asset with wrong id",
            )
        )


def test_transfer_asa_to_another_account(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    test_asset_id = generate_test_asset(algorand, funded_account, 100)
    second_account = algorand.account.random()
    algorand.account.ensure_funded(
        account_to_fund=second_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    with pytest.raises(Exception, match="account asset info not found"):
        algorand.asset.get_account_information(second_account, test_asset_id)

    algorand.send.asset_opt_in(
        AssetOptInParams(
            sender=second_account.address,
            asset_id=test_asset_id,
        )
    )

    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=funded_account.address,
            receiver=second_account.address,
            asset_id=test_asset_id,
            amount=5,
            note=b"Transfer 5 assets with id %d" % test_asset_id,
        )
    )

    second_account_info = algorand.asset.get_account_information(second_account, test_asset_id)
    assert second_account_info.balance == 5

    test_account_info = algorand.asset.get_account_information(funded_account, test_asset_id)
    assert test_account_info.balance == 95


def test_transfer_asa_from_revocation_target(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    test_asset_id = generate_test_asset(algorand, funded_account, 100)
    second_account = algorand.account.random()
    clawback_account = algorand.account.random()

    algorand.account.ensure_funded(
        account_to_fund=second_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )
    algorand.account.ensure_funded(
        account_to_fund=clawback_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    algorand.send.asset_opt_in(
        AssetOptInParams(
            sender=second_account.address,
            asset_id=test_asset_id,
        )
    )

    algorand.send.asset_opt_in(
        AssetOptInParams(
            sender=clawback_account.address,
            asset_id=test_asset_id,
        )
    )

    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=funded_account.address,
            receiver=clawback_account.address,
            asset_id=test_asset_id,
            amount=5,
            note=b"Transfer 5 assets with id %d" % test_asset_id,
        )
    )

    clawback_from_info = algorand.asset.get_account_information(clawback_account, test_asset_id)
    assert clawback_from_info.balance == 5

    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=funded_account.address,
            receiver=second_account.address,
            asset_id=test_asset_id,
            amount=5,
            note=b"Transfer 5 assets with id %d" % test_asset_id,
            clawback_target=clawback_account.address,
        )
    )

    second_account_info = algorand.asset.get_account_information(second_account, test_asset_id)
    assert second_account_info.balance == 5

    clawback_account_info = algorand.asset.get_account_information(clawback_account, test_asset_id)
    assert clawback_account_info.balance == 0

    test_account_info = algorand.asset.get_account_information(funded_account, test_asset_id)
    assert test_account_info.balance == 95


MINIMUM_BALANCE = AlgoAmount.from_micro_algo(
    100_000
)  # see https://developer.algorand.org/docs/get-details/accounts/#minimum-balance


def test_ensure_funded(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    test_account = algorand.account.random()
    response = algorand.account.ensure_funded(
        account_to_fund=test_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_algo(1),
    )
    assert response is not None

    to_account_info = algorand.account.get_information(test_account)
    assert to_account_info.amount == MINIMUM_BALANCE + AlgoAmount.from_algo(1)


def test_ensure_funded_uses_dispenser_by_default(
    algorand: AlgorandClient,
) -> None:
    second_account = algorand.account.random()
    dispenser = algorand.account.dispenser_from_environment()

    result = algorand.account.ensure_funded_from_environment(
        account_to_fund=second_account,
        min_spending_balance=AlgoAmount.from_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )

    assert result is not None
    assert result.transaction.payment is not None
    assert result.transaction.payment.sender == dispenser.address

    account_info = algorand.account.get_information(second_account)
    assert account_info.amount == MINIMUM_BALANCE + AlgoAmount.from_algo(1)


def test_ensure_funded_respects_minimum_funding_increment(
    algorand: AlgorandClient, funded_account: SigningAccount
) -> None:
    test_account = algorand.account.random()
    response = algorand.account.ensure_funded(
        account_to_fund=test_account,
        dispenser_account=funded_account,
        min_spending_balance=AlgoAmount.from_micro_algo(1),
        min_funding_increment=AlgoAmount.from_algo(1),
    )
    assert response is not None

    to_account_info = algorand.account.get_information(test_account)
    assert to_account_info.amount == AlgoAmount.from_algo(1)


def test_ensure_funded_testnet_api_success(monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock) -> None:
    algorand = AlgorandClient.testnet()
    account_to_fund = algorand.account.random()
    monkeypatch.setenv(
        "ALGOKIT_DISPENSER_ACCESS_TOKEN",
        "dummy",
    )
    httpx_mock.add_response(
        url=f"{DispenserApiConfig.BASE_URL}/fund/0",
        method="POST",
        json={"amount": 1, "txID": "dummy_tx_id"},
    )

    result = algorand.account.ensure_funded_from_testnet_dispenser_api(
        account_to_fund=account_to_fund,
        dispenser_client=TestNetDispenserApiClient(),
        min_spending_balance=AlgoAmount.from_micro_algo(1),
    )
    assert result is not None
    assert result.transaction_id == "dummy_tx_id"
    assert result.amount_funded == AlgoAmount.from_micro_algo(1)


def test_ensure_funded_testnet_api_bad_response(monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock) -> None:
    algorand = AlgorandClient.testnet()
    account_to_fund = algorand.account.random()
    monkeypatch.setenv(
        "ALGOKIT_DISPENSER_ACCESS_TOKEN",
        "dummy",
    )
    httpx_mock.add_exception(
        httpx.HTTPStatusError(
            "Limit exceeded",
            request=httpx.Request("POST", f"{DispenserApiConfig.BASE_URL}/fund"),
            response=httpx.Response(
                400,
                request=httpx.Request("POST", f"{DispenserApiConfig.BASE_URL}/fund"),
                json={
                    "code": "fund_limit_exceeded",
                    "limit": 10_000_000,
                    "resetsAt": "2023-09-19T10:07:34.024Z",
                },
            ),
        ),
        url=f"{DispenserApiConfig.BASE_URL}/fund/0",
        method="POST",
    )

    with pytest.raises(Exception, match="fund_limit_exceeded"):
        algorand.account.ensure_funded_from_testnet_dispenser_api(
            account_to_fund=account_to_fund,
            dispenser_client=TestNetDispenserApiClient(),
            min_spending_balance=AlgoAmount.from_micro_algo(1),
        )


def test_rekey_works(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    second_account = algorand.account.random()

    algorand.account.rekey_account(funded_account.address, second_account, note=b"rekey")

    # This will throw if the rekey wasn't successful
    algorand.send.payment(
        PaymentParams(
            sender=funded_account.address,
            receiver=funded_account.address,
            amount=AlgoAmount.from_micro_algo(1),
            signer=second_account.signer,
        )
    )
