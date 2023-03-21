import dataclasses

from algosdk.transaction import PaymentTxn
from algosdk.v2client.algod import AlgodClient

from algokit_utils.models import Account
from algokit_utils.transaction import send_transaction


@dataclasses.dataclass
class TransferParameters:
    from_account: Account
    to_address: str
    amount: int  # micro algos
    note: str | None = None
    skip_sending: bool = False
    skip_waiting: bool = False
    max_fee_in_algos: int | None = None  # TODO: micro algos?


def transfer(transfer_parameters: TransferParameters, client: AlgodClient) -> PaymentTxn:
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

    if not transfer_parameters.skip_sending:
        return send_transaction(
            client,
            transaction,
            transfer_parameters.from_account,
            skip_waiting=transfer_parameters.skip_waiting,
            max_fee=transfer_parameters.max_fee_in_algos or 0.02,
        )

    return transaction
