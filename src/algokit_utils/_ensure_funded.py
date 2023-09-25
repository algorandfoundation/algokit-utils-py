import os
from dataclasses import dataclass

from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.transaction import PaymentTxn, SuggestedParams
from algosdk.v2client.algod import AlgodClient

from algokit_utils._dispenser_api import DISPENSER_ACCESS_TOKEN_KEY, DispenserAssetName, process_dispenser_fund_request
from algokit_utils._transfer import TransferParameters, transfer
from algokit_utils.account import get_dispenser_account
from algokit_utils.models import Account
from algokit_utils.network_clients import is_testnet


@dataclass(kw_only=True)
class EnsureBalanceParameters:
    """Parameters for ensuring an account has a minimum number of µALGOs"""

    account_to_fund: Account | AccountTransactionSigner | str
    """The account address that will receive the µALGOs"""

    min_spending_balance_micro_algos: int
    """The minimum balance of ALGOs that the account should have available to spend (i.e. on top of
    minimum balance requirement)"""

    min_funding_increment_micro_algos: int = 0
    """When issuing a funding amount, the minimum amount to transfer (avoids many small transfers if this gets
    called often on an active account)"""

    funding_source: Account | AccountTransactionSigner | None = None
    """The account (with private key) or signer that will send the µALGOs,
    will use `get_dispenser_account` by default"""

    suggested_params: SuggestedParams | None = None
    """(optional) transaction parameters"""

    note: str | bytes | None = None
    """The (optional) transaction note, default: "Funding account to meet minimum requirement"""

    fee_micro_algos: int | None = None
    """(optional) The flat fee you want to pay, useful for covering extra fees in a transaction group or app call"""

    max_fee_micro_algos: int | None = None
    """(optional)The maximum fee that you are happy to pay (default: unbounded) -
    if this is set it's possible the transaction could get rejected during network congestion"""

    use_dispenser_api: bool = False
    """If True, will use the dispenser API to fund the account if it's on TestNet"""


def _get_address_to_fund(parameters: EnsureBalanceParameters) -> str:
    if isinstance(parameters.account_to_fund, str):
        return parameters.account_to_fund
    else:
        return str(address_from_private_key(parameters.account_to_fund.private_key))  # type: ignore[no-untyped-call]


def _get_account_info(client: AlgodClient, address_to_fund: str) -> dict:
    account_info = client.account_info(address_to_fund)
    assert isinstance(account_info, dict)
    return account_info


def _calculate_fund_amount(
    parameters: EnsureBalanceParameters, current_spending_balance_micro_algos: int
) -> int | None:
    if parameters.min_spending_balance_micro_algos > current_spending_balance_micro_algos:
        min_fund_amount_micro_algos = parameters.min_spending_balance_micro_algos - current_spending_balance_micro_algos
        return max(min_fund_amount_micro_algos, parameters.min_funding_increment_micro_algos)
    else:
        return None


def _fund_using_dispenser_api(address_to_fund: str, fund_amount_micro_algos: int) -> str | None:
    ci_access_token = os.environ.get(DISPENSER_ACCESS_TOKEN_KEY)

    if not ci_access_token:
        raise Exception(
            f"Can't use dispenser API to fund account {address_to_fund} "
            "via AlgoKit TestNet Dispenser API because "
            f"environment variable {DISPENSER_ACCESS_TOKEN_KEY} is not set"
        )

    return process_dispenser_fund_request(
        address=address_to_fund,
        amount=fund_amount_micro_algos,
        asset_id=DispenserAssetName.ALGO,
        auth_token=ci_access_token,
    )


def _fund_using_transfer(
    client: AlgodClient, parameters: EnsureBalanceParameters, address_to_fund: str, fund_amount_micro_algos: int
) -> PaymentTxn:
    funding_source = parameters.funding_source or get_dispenser_account(client)
    return transfer(
        client,
        TransferParameters(
            from_account=funding_source,
            to_address=address_to_fund,
            micro_algos=fund_amount_micro_algos,
            note=parameters.note or "Funding account to meet minimum requirement",
            suggested_params=parameters.suggested_params,
            max_fee_micro_algos=parameters.max_fee_micro_algos,
            fee_micro_algos=parameters.fee_micro_algos,
        ),
    )


def ensure_funded(
    client: AlgodClient,
    parameters: EnsureBalanceParameters,
) -> PaymentTxn | str | None:
    """
    Funds a given account using a funding source such that it has a certain amount of algos free to spend
    (accounting for ALGOs locked in minimum balance requirement)
    see <https://developer.algorand.org/docs/get-details/accounts/#minimum-balance>


    Args:
        client (AlgodClient): An instance of the AlgodClient class from the AlgoSDK library.
        parameters (EnsureBalanceParameters): An instance of the EnsureBalanceParameters class that
        specifies the account to fund and the minimum spending balance.

    Returns:
        PaymentTxn | str | None: If funds are needed, the function returns a payment transaction or a
        string indicating that the dispenser API was used. If no funds are needed, the function returns None.
    """

    address_to_fund = _get_address_to_fund(parameters)
    account_info = _get_account_info(client, address_to_fund)
    balance_micro_algos = account_info.get("amount", 0)
    minimum_balance_micro_algos = account_info.get("min-balance", 0)
    current_spending_balance_micro_algos = balance_micro_algos - minimum_balance_micro_algos
    fund_amount_micro_algos = _calculate_fund_amount(parameters, current_spending_balance_micro_algos)

    if fund_amount_micro_algos is not None:
        if is_testnet(client) and parameters.use_dispenser_api:
            return _fund_using_dispenser_api(address_to_fund, fund_amount_micro_algos)
        else:
            return _fund_using_transfer(client, parameters, address_to_fund, fund_amount_micro_algos)

    return None
