from __future__ import annotations

from algokit_algod_client import (
    AlgodClient,
)
from algokit_algod_client.models import (
    SimulateRequest,
    SimulateRequestTransactionGroup,
    SimulateTraceConfig,
)
from algokit_transact import PaymentTransactionFields, SignedTransaction, Transaction, TransactionType


def test_simulate_transactions(algod_client: AlgodClient) -> None:
    # Build two simple unsigned transactions using algokit-transact helpers
    sender = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
    recv = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
    t1 = Transaction(
        transaction_type=TransactionType.Payment,
        sender=sender,
        first_valid=1,
        last_valid=1000,
        payment=PaymentTransactionFields(receiver=recv, amount=0, close_remainder_to=None),
    )
    t2 = t1

    req = SimulateRequest(
        txn_groups=[
            SimulateRequestTransactionGroup(
                txns=[
                    SignedTransaction(transaction=t1),
                    SignedTransaction(transaction=t2),
                ]
            )
        ],
        allow_empty_signatures=True,
        allow_more_logging=True,
        allow_unnamed_resources=True,
        round_=0,
        extra_opcode_budget=1000,
        exec_trace_config=SimulateTraceConfig(enable=True, stack_change=True, scratch_change=True, state_change=True),
        fix_signers=True,
    )

    resp = algod_client.simulate_transaction(
        body=req,
    )
    assert len(resp.txn_groups) == 1
    assert len(resp.txn_groups[0].txn_results) == 2
