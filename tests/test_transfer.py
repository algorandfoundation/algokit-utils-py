from typing import TYPE_CHECKING

import pytest
from algokit_utils import (
    Account,
    EnsureBalanceParameters,
    TransferParameters,
    create_kmd_wallet_account,
    ensure_funded,
    get_dispenser_account,
    transfer,
)
from algosdk.util import algos_to_microalgos

from tests.conftest import check_output_stability, get_unique_name

if TYPE_CHECKING:
    from algosdk.kmd import KMDClient
    from algosdk.v2client.algod import AlgodClient


MINIMUM_BALANCE = 100_000  # see https://developer.algorand.org/docs/get-details/accounts/#minimum-balance


@pytest.fixture()
def to_account(kmd_client: "KMDClient") -> Account:
    return create_kmd_wallet_account(kmd_client, get_unique_name())


def test_transfer_algo(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    requested_amount = 100_000
    transfer(
        algod_client,
        TransferParameters(
            from_account=funded_account,
            to_address=to_account.address,
            micro_algos=requested_amount,
        ),
    )

    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == requested_amount


def test_transfer_algo_max_fee_fails(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    requested_amount = 100_000
    max_fee = 123

    with pytest.raises(Exception, match="Cancelled transaction due to high network congestion fees") as ex:
        transfer(
            algod_client,
            TransferParameters(
                from_account=funded_account,
                to_address=to_account.address,
                micro_algos=requested_amount,
                max_fee_micro_algos=max_fee,
            ),
        )

    check_output_stability(str(ex.value))


def test_transfer_algo_fee(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    requested_amount = 100_000
    fee = 1234
    txn = transfer(
        algod_client,
        TransferParameters(
            from_account=funded_account,
            to_address=to_account.address,
            micro_algos=requested_amount,
            fee_micro_algos=fee,
        ),
    )

    assert txn.fee == fee


def test_transfer_asa_receiver_not_optin(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    transfer_asset()


#     const { algod, testAccount } = localnet.context
#     const dummyAssetID = await generateTestAsset(algod, testAccount, 100)
#     const secondAccount = algosdk.generateAccount()

#     try {
#       await algokit.transferAsset(
#         {
#           from: testAccount,
#           to: secondAccount.addr,
#           assetID: dummyAssetID,
#           amount: 5,
#           note: `Transfer 5 assets wit id ${dummyAssetID}`,
#         },
#         algod,
#       )
#     } catch (e: unknown) {
#       expect((e as Error).name).toEqual('URLTokenBaseHTTPError')
#       expect((e as Error).message).toContain('receiver error: must optin')
#     }
#   }, 10e6)

#   test('Transfer ASA, sender is not opted in', async () => {
#     const { algod, testAccount, kmd } = localnet.context
#     const dummyAssetID = await generateTestAsset(algod, testAccount, 100)
#     const secondAccount = algosdk.generateAccount()

#     await assureFundsAndOptIn(algod, secondAccount, dummyAssetID, kmd)

#     try {
#       await algokit.transferAsset(
#         {
#           from: testAccount,
#           to: secondAccount.addr,
#           assetID: dummyAssetID,
#           amount: 5,
#           note: `Transfer 5 assets wit id ${dummyAssetID}`,
#         },
#         algod,
#       )
#     } catch (e: unknown) {
#       expect((e as Error).name).toEqual('URLTokenBaseHTTPError')
#       expect((e as Error).message).toContain('sender error: must optin')
#     }
#   }, 10e6)

#   test('Transfer ASA, asset doesnt exist', async () => {
#     const { algod, testAccount, kmd } = localnet.context
#     const dummyAssetID = await generateTestAsset(algod, testAccount, 100)
#     const secondAccount = algosdk.generateAccount()

#     await assureFundsAndOptIn(algod, secondAccount, dummyAssetID, kmd)
#     await optIn(algod, testAccount, dummyAssetID)
#     try {
#       await algokit.transferAsset(
#         {
#           from: testAccount,
#           to: secondAccount.addr,
#           assetID: 1,
#           amount: 5,
#           note: `Transfer asset with wrong id`,
#         },
#         algod,
#       )
#     } catch (e: unknown) {
#       expect((e as Error).name).toEqual('URLTokenBaseHTTPError')
#       expect((e as Error).message).toContain('asset 1 missing from')
#     }
#   }, 10e6)

#   test('Transfer ASA, without sending', async () => {
#     const { algod, testAccount, kmd } = localnet.context
#     const dummyAssetID = await generateTestAsset(algod, testAccount, 100)
#     const secondAccount = algosdk.generateAccount()

#     await assureFundsAndOptIn(algod, secondAccount, dummyAssetID, kmd)
#     await optIn(algod, testAccount, dummyAssetID)
#     const response = await algokit.transferAsset(
#       {
#         from: testAccount,
#         to: secondAccount.addr,
#         assetID: 1,
#         amount: 5,
#         note: `Transfer asset with wrong id`,
#         skipSending: true,
#       },
#       algod,
#     )

#     expect(response.transaction).toBeDefined()
#     expect(response.confirmation).toBeUndefined()
#   }, 10e6)

#   test('Transfer ASA, asset is transfered to another account', async () => {
#     const { algod, testAccount, kmd } = localnet.context
#     const dummyAssetID = await generateTestAsset(algod, testAccount, 100)
#     const secondAccount = algosdk.generateAccount()

#     await assureFundsAndOptIn(algod, secondAccount, dummyAssetID, kmd)
#     await optIn(algod, testAccount, dummyAssetID)

#     await algokit.transferAsset(
#       {
#         from: testAccount,
#         to: secondAccount.addr,
#         assetID: dummyAssetID,
#         amount: 5,
#         note: `Transfer 5 assets wit id ${dummyAssetID}`,
#       },
#       algod,
#     )

#     const secondAccountInfo = await algod.accountAssetInformation(secondAccount.addr, dummyAssetID).do()
#     expect(secondAccountInfo['asset-holding']['amount']).toBe(5)

#     const testAccountInfo = await algod.accountAssetInformation(testAccount.addr, dummyAssetID).do()
#     expect(testAccountInfo['asset-holding']['amount']).toBe(95)
#   }, 10e6)

#   test('Transfer ASA, asset is transfered to another account from revocationTarget', async () => {
#     const { algod, testAccount, kmd } = localnet.context
#     const dummyAssetID = await generateTestAsset(algod, testAccount, 100)
#     const secondAccount = algosdk.generateAccount()
#     const clawbackAccount = algosdk.generateAccount()

#     await assureFundsAndOptIn(algod, secondAccount, dummyAssetID, kmd)
#     await assureFundsAndOptIn(algod, clawbackAccount, dummyAssetID, kmd)
#     await optIn(algod, testAccount, dummyAssetID)

#     await algokit.transferAsset(
#       {
#         from: testAccount,
#         to: clawbackAccount.addr,
#         assetID: dummyAssetID,
#         amount: 5,
#         note: `Transfer 5 assets wit id ${dummyAssetID}`,
#       },
#       algod,
#     )

#     const clawbackFromInfo = await algod.accountAssetInformation(clawbackAccount.addr, dummyAssetID).do()
#     expect(clawbackFromInfo['asset-holding']['amount']).toBe(5)

#     await algokit.transferAsset(
#       {
#         from: testAccount,
#         to: secondAccount.addr,
#         assetID: dummyAssetID,
#         amount: 5,
#         note: `Transfer 5 assets wit id ${dummyAssetID}`,
#         clawbackFrom: clawbackAccount,
#       },
#       algod,
#     )

#     const secondAccountInfo = await algod.accountAssetInformation(secondAccount.addr, dummyAssetID).do()
#     expect(secondAccountInfo['asset-holding']['amount']).toBe(5)

#     const clawbackAccountInfo = await algod.accountAssetInformation(clawbackAccount.addr, dummyAssetID).do()
#     expect(clawbackAccountInfo['asset-holding']['amount']).toBe(0)

#     const testAccountInfo = await algod.accountAssetInformation(testAccount.addr, dummyAssetID).do()
#     expect(testAccountInfo['asset-holding']['amount']).toBe(95)
#   }, 10e6)


def test_ensure_funded(algod_client: "AlgodClient", to_account: Account, funded_account: Account) -> None:
    parameters = EnsureBalanceParameters(
        funding_source=funded_account,
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
    )
    response = ensure_funded(algod_client, parameters)
    assert response is not None

    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == MINIMUM_BALANCE + 1


def test_ensure_funded_uses_dispenser_by_default(algod_client: "AlgodClient", to_account: Account) -> None:
    dispenser = get_dispenser_account(algod_client)
    parameters = EnsureBalanceParameters(
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
    )
    response = ensure_funded(algod_client, parameters)
    assert response is not None

    assert response.sender == dispenser.address
    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == MINIMUM_BALANCE + 1


def test_ensure_funded_correct_amount(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    parameters = EnsureBalanceParameters(
        funding_source=funded_account,
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
    )
    response = ensure_funded(algod_client, parameters)
    assert response is not None

    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == MINIMUM_BALANCE + 1


def test_ensure_funded_respects_minimum_funding(
    algod_client: "AlgodClient", to_account: Account, funded_account: Account
) -> None:
    parameters = EnsureBalanceParameters(
        funding_source=funded_account,
        account_to_fund=to_account,
        min_spending_balance_micro_algos=1,
        min_funding_increment_micro_algos=algos_to_microalgos(1),  # type: ignore[no-untyped-call]
    )
    response = ensure_funded(algod_client, parameters)
    assert response is not None

    to_account_info = algod_client.account_info(to_account.address)
    assert isinstance(to_account_info, dict)
    actual_amount = to_account_info.get("amount")
    assert actual_amount == algos_to_microalgos(1)  # type: ignore[no-untyped-call]
