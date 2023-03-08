import logging

from algosdk.transaction import PaymentTxn
from algosdk.v2client.algod import AlgodClient

from algokit_utils.models import Account

logger = logging.getLogger(__name__)


def send_transaction(
    client: AlgodClient,
    transaction: PaymentTxn,
    from_account: Account,  # TODO: logic signature support
    *,
    skip_waiting: bool,
    max_fee: float,
) -> PaymentTxn:
    # TODO: cap fee

    signed_transaction = transaction.sign(from_account.private_key)  # type: ignore[no-untyped-call]
    client.send_transaction(signed_transaction)  # type: ignore[no-untyped-call]

    txid = transaction.get_txid()  # type: ignore[no-untyped-call]
    logger.debug(f"Sent transaction {txid} type={transaction.type} from {from_account.address}")

    if not skip_waiting:
        # TODO: wait for confirmation
        pass

    return transaction
