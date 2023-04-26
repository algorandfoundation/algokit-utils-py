import dataclasses
import logging
from typing import TYPE_CHECKING

import algosdk.transaction
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.transaction import PaymentTxn, SuggestedParams

from algokit_utils.models import Account

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

__all__ = ["EnsureBalanceParameters", "TransferParameters", "ensure_funded", "transfer"]
logger = logging.getLogger(__name__)


@dataclasses.dataclass(kw_only=True)
class TransferParameters:
    """Parameters for transferring µALGOs between accounts"""

    from_account: Account | AccountTransactionSigner
    """The account (with private key) or signer that will send the µALGOs"""
    to_address: str
    """The account address that will receive the µALGOs"""
    micro_algos: int
    """The amount of µALGOs to send"""
    suggested_params: SuggestedParams | None = None
    """(optional) transaction parameters"""
    note: str | bytes | None = None
    """(optional) transaction note"""
    fee_micro_algos: int | None = None
    """(optional) The flat fee you want to pay, useful for covering extra fees in a transaction group or app call"""
    max_fee_micro_algos: int | None = None
    """(optional)The maximum fee that you are happy to pay (default: unbounded) -
    if this is set it's possible the transaction could get rejected during network congestion"""


@dataclasses.dataclass(kw_only=True)
class EnsureBalanceParameters:
    """Parameters for ensuring an account has a minimum number of µALGOs"""

    account_to_fund: Account | AccountTransactionSigner | str
    """The account address that will receive the µALGOs"""

    funding_source: Account | AccountTransactionSigner
    """The account (with private key) or signer that will send the µALGOs"""

    min_spending_balance_micro_algos: int
    """The minimum balance of ALGOs that the account should have available to spend (i.e. on top of
    minimum balance requirement)"""

    min_funding_increment_micro_algos: int = 0
    """When issuing a funding amount, the minimum amount to transfer (avoids many small transfers if this gets
    called often on an active account)"""

    suggested_params: SuggestedParams | None = None
    """(optional) transaction parameters"""

    note: str | bytes | None = None
    """The (optional) transaction note, default: "Funding account to meet minimum requirement"""

    fee_micro_algos: int | None = None
    """(optional) The flat fee you want to pay, useful for covering extra fees in a transaction group or app call"""

    max_fee_micro_algos: int | None = None
    """(optional)The maximum fee that you are happy to pay (default: unbounded) -
    if this is set it's possible the transaction could get rejected during network congestion"""


def _check_fee(transaction: PaymentTxn, max_fee: int | None) -> None:
    if max_fee is not None:
        # Once a transaction has been constructed by algosdk, transaction.fee indicates what the total transaction fee
        # Will be based on the current suggested fee-per-byte value.
        if transaction.fee > max_fee:
            raise Exception(
                f"Cancelled transaction due to high network congestion fees. "
                f"Algorand suggested fees would cause this transaction to cost {transaction.fee} µALGOs. "
                f"Cap for this transaction is {max_fee} µALGOs."
            )
        if transaction.fee > algosdk.constants.MIN_TXN_FEE:
            logger.warning(
                f"Algorand network congestion fees are in effect. "
                f"This transaction will incur a fee of {transaction.fee} µALGOs."
            )


def transfer(client: "AlgodClient", parameters: TransferParameters) -> PaymentTxn:
    """Transfer µALGOs between accounts"""

    suggested_params = parameters.suggested_params or client.suggested_params()
    from_account = parameters.from_account
    sender = address_from_private_key(from_account.private_key)  # type: ignore[no-untyped-call]
    transaction = PaymentTxn(
        sender=sender,
        receiver=parameters.to_address,
        amt=parameters.micro_algos,
        note=parameters.note.encode("utf-8") if isinstance(parameters.note, str) else parameters.note,
        sp=suggested_params,
    )  # type: ignore[no-untyped-call]
    if parameters.fee_micro_algos:
        transaction.fee = parameters.fee_micro_algos

    if not suggested_params.flat_fee:
        _check_fee(transaction, parameters.max_fee_micro_algos)
    signed_transaction = transaction.sign(from_account.private_key)  # type: ignore[no-untyped-call]
    client.send_transaction(signed_transaction)

    txid = transaction.get_txid()  # type: ignore[no-untyped-call]
    logger.debug(
        f"Sent transaction {txid} type={transaction.type} from "
        f"{address_from_private_key(from_account.private_key)}"  # type: ignore[no-untyped-call]
    )

    return transaction


def ensure_funded(
    client: "AlgodClient",
    parameters: EnsureBalanceParameters,
) -> None | PaymentTxn:
    """
    Funds a given account using a funding source such that it has a certain amount of algos free to spend
    (accounting for ALGOs locked in minimum balance requirement)
    see <https://developer.algorand.org/docs/get-details/accounts/#minimum-balance>

    :return None | PaymentTxn: None if balance was sufficient or the payment transaction used to increase the balance
    """
    sender_address = address_from_private_key(parameters.funding_source.private_key)  # type: ignore[no-untyped-call]
    address_to_fund = (
        parameters.account_to_fund
        if isinstance(parameters.account_to_fund, str)
        else address_from_private_key(parameters.account_to_fund.private_key)  # type: ignore[no-untyped-call]
    )

    account_info = client.account_info(address_to_fund)
    assert isinstance(account_info, dict)

    balance_micro_algos = account_info.get("amount", 0)
    minimum_balance_micro_algos = account_info.get("min-balance")
    current_spending_balance_micro_algos = balance_micro_algos - minimum_balance_micro_algos
    if parameters.min_spending_balance_micro_algos > current_spending_balance_micro_algos:
        min_fund_amount_micro_algos = parameters.min_spending_balance_micro_algos - current_spending_balance_micro_algos
        fund_amount_micro_algos = max(min_fund_amount_micro_algos, parameters.min_funding_increment_micro_algos)
        logger.info(
            f"Funding {address_to_fund} {fund_amount_micro_algos}µ from {sender_address} to reach "
            f"minimum spend amount of {parameters.min_spending_balance_micro_algos}µ (balance = "
            f"{balance_micro_algos}µ, requirement = {minimum_balance_micro_algos}µ)"
        )
        return transfer(
            client,
            TransferParameters(
                from_account=parameters.funding_source,
                to_address=address_to_fund,
                micro_algos=fund_amount_micro_algos,
                note=parameters.note or "Funding account to meet minimum requirement",
                suggested_params=parameters.suggested_params,
                max_fee_micro_algos=parameters.max_fee_micro_algos,
                fee_micro_algos=parameters.fee_micro_algos,
            ),
        )

    return None
