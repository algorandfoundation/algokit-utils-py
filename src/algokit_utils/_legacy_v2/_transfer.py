import dataclasses
import logging
from typing import TYPE_CHECKING

import algosdk.transaction
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.transaction import AssetTransferTxn, PaymentTxn, SuggestedParams
from typing_extensions import deprecated

from algokit_utils._legacy_v2.models import Account

if TYPE_CHECKING:
    from algosdk.v2client.algod import AlgodClient

__all__ = ["TransferAssetParameters", "TransferParameters", "transfer", "transfer_asset"]
logger = logging.getLogger(__name__)


@dataclasses.dataclass(kw_only=True)
class TransferParametersBase:
    """Parameters for transferring µALGOs between accounts.

    This class contains the base parameters needed for transferring µALGOs between Algorand accounts.

    :ivar from_account: The account (with private key) or signer that will send the µALGOs
    :ivar to_address: The account address that will receive the µALGOs
    :ivar suggested_params: Transaction parameters, defaults to None
    :ivar note: Transaction note, defaults to None
    :ivar fee_micro_algos: The flat fee you want to pay, useful for covering extra fees in a transaction group or app call, defaults to None
    :ivar max_fee_micro_algos: The maximum fee that you are happy to pay - if this is set it's possible the transaction could get rejected during network congestion, defaults to None
    """

    from_account: Account | AccountTransactionSigner
    to_address: str
    suggested_params: SuggestedParams | None = None
    note: str | bytes | None = None
    fee_micro_algos: int | None = None
    max_fee_micro_algos: int | None = None


@deprecated("Use `algorand.send.payment(...)` / `algorand.create_transaction.payment(...)` instead")
@dataclasses.dataclass(kw_only=True)
class TransferParameters(TransferParametersBase):
    """Parameters for transferring µALGOs between accounts"""

    micro_algos: int


@deprecated("Use `algorand.send.asset_transfer(...)` / `algorand.create_transaction.asset_transfer(...)` instead")
@dataclasses.dataclass(kw_only=True)
class TransferAssetParameters(TransferParametersBase):
    """Parameters for transferring assets between accounts.

    Defines the parameters needed to transfer Algorand Standard Assets (ASAs) between accounts.

    :param asset_id: The asset id that will be transferred
    :param amount: The amount of the asset to send
    :param clawback_from: An address of a target account from which to perform a clawback operation. Please note, in such cases senderAccount must be equal to clawback field on ASA metadata, defaults to None
    """

    asset_id: int
    amount: int
    clawback_from: str | None = None


def _check_fee(transaction: PaymentTxn | AssetTransferTxn, max_fee: int | None) -> None:
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


@deprecated("Use `algorand.send.payment(...)` / `algorand.create_transaction.payment(...)` instead")
def transfer(client: "AlgodClient", parameters: TransferParameters) -> PaymentTxn:
    """Transfer µALGOs between accounts"""

    params = parameters
    params.suggested_params = parameters.suggested_params or client.suggested_params()
    from_account = params.from_account
    sender = _get_address(from_account)
    transaction = PaymentTxn(
        sender=sender,
        receiver=params.to_address,
        amt=params.micro_algos,
        note=params.note.encode("utf-8") if isinstance(params.note, str) else params.note,
        sp=params.suggested_params,
    )

    result = _send_transaction(client=client, transaction=transaction, parameters=params)
    assert isinstance(result, PaymentTxn)
    return result


@deprecated("Use `algorand.send.asset_transfer(...)` / `algorand.create_transaction.asset_transfer(...)` instead")
def transfer_asset(client: "AlgodClient", parameters: TransferAssetParameters) -> AssetTransferTxn:
    """Transfer assets between accounts"""

    params = parameters
    params.suggested_params = parameters.suggested_params or client.suggested_params()
    sender = _get_address(parameters.from_account)
    suggested_params = parameters.suggested_params or client.suggested_params()
    xfer_txn = AssetTransferTxn(
        sp=suggested_params,
        sender=sender,
        receiver=params.to_address,
        close_assets_to=None,
        revocation_target=params.clawback_from,
        amt=params.amount,
        note=params.note,
        index=params.asset_id,
        rekey_to=None,
    )

    result = _send_transaction(client=client, transaction=xfer_txn, parameters=params)
    assert isinstance(result, AssetTransferTxn)
    return result


def _send_transaction(
    client: "AlgodClient",
    transaction: PaymentTxn | AssetTransferTxn,
    parameters: TransferAssetParameters | TransferParameters,
) -> PaymentTxn | AssetTransferTxn:
    if parameters.fee_micro_algos:
        transaction.fee = parameters.fee_micro_algos

    if parameters.suggested_params is not None and not parameters.suggested_params.flat_fee:
        _check_fee(transaction, parameters.max_fee_micro_algos)

    signed_transaction = transaction.sign(parameters.from_account.private_key)  # type: ignore[no-untyped-call]
    client.send_transaction(signed_transaction)

    txid = transaction.get_txid()  # type: ignore[no-untyped-call]
    logger.debug(f"Sent transaction {txid} type={transaction.type} from {_get_address(parameters.from_account)}")

    return transaction


def _get_address(account: Account | AccountTransactionSigner) -> str:
    if type(account) is Account:
        return account.address
    else:
        address = address_from_private_key(account.private_key)
        return str(address)
