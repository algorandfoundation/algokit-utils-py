import dataclasses
import logging

from algosdk.transaction import PaymentTxn
from algosdk.v2client.algod import AlgodClient

from algokit_utils.models import Account

__all__ = ["TransferParameters", "transfer"]
logger = logging.getLogger(__name__)


@dataclasses.dataclass(kw_only=True)
class TransferParameters:
    from_account: Account
    to_address: str
    amount: int
    note: str | None = None
    max_fee_in_algos: float | None = None


def transfer(transfer_parameters: TransferParameters, client: AlgodClient) -> tuple[PaymentTxn, str]:
    suggested_params = client.suggested_params()
    transaction = PaymentTxn(
        sender=transfer_parameters.from_account.address,
        sp=suggested_params,
        receiver=transfer_parameters.to_address,
        amt=transfer_parameters.amount,
        close_remainder_to=None,
        note=transfer_parameters.note.encode("utf-8") if transfer_parameters.note else None,
        rekey_to=None,
    )  # type: ignore[no-untyped-call]
    # TODO: max fee
    from_account = transfer_parameters.from_account
    signed_transaction = transaction.sign(from_account.private_key)  # type: ignore[no-untyped-call]
    send_response = client.send_transaction(signed_transaction)

    txid = transaction.get_txid()  # type: ignore[no-untyped-call]
    logger.debug(f"Sent transaction {txid} type={transaction.type} from {from_account.address}")

    return transaction, send_response
