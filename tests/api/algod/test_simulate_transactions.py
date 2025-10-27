from __future__ import annotations

import copy

import msgpack
from algod_client.client import AlgodClient
from algod_client.models import SimulateRequest, SimulateRequestTransactionGroup, SimulateTraceConfig
from algokit_transact import PaymentTransactionFields, SignedTransaction, Transaction, TransactionType
from pytest_httpx import HTTPXMock


def test_simulate_transactions(algod_client: AlgodClient, httpx_mock: HTTPXMock) -> None:
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

    stxns = [
        SignedTransaction(
            transaction=t1, signature=None, multi_signature=None, logic_signature=None, auth_address=None
        ),
        SignedTransaction(
            transaction=t2, signature=None, multi_signature=None, logic_signature=None, auth_address=None
        ),
    ]

    group = SimulateRequestTransactionGroup(txns=stxns)
    trace = SimulateTraceConfig(enable=True, stack_change=True, scratch_change=True, state_change=True)
    req = SimulateRequest(
        txn_groups=[group],
        allow_empty_signatures=True,
        allow_more_logging=True,
        allow_unnamed_resources=True,
        round_=0,
        extra_opcode_budget=1000,
        exec_trace_config=trace,
        fix_signers=True,
    )

    # Stub the algod simulate endpoint with a msgpack payload matching the request
    address_bytes = bytes([1]) * 32
    receiver_bytes = bytes([2]) * 32
    stub_transaction = {
        "type": "pay",
        "snd": address_bytes,
        "fv": 1,
        "lv": 1000,
        "amt": 0,
        "rcv": receiver_bytes,
    }
    stub_signed_transaction = {"txn": stub_transaction}
    stub_pending_txn = {"pool-error": "", "txn": stub_signed_transaction}
    stub_txn_result = {"txn-result": stub_pending_txn}
    response_payload = {
        "last-round": 123,
        "version": 1,
        "txn-groups": [
            {
                "txn-results": [
                    stub_txn_result,
                    copy.deepcopy(stub_txn_result),
                ]
            }
        ],
    }
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:4001/v2/transactions/simulate?format=msgpack",
        content=msgpack.packb(response_payload, use_bin_type=True),
        headers={"content-type": "application/msgpack"},
    )

    resp = algod_client.simulate_transaction(body=req, response_format="msgpack")
    assert len(resp.txn_groups) == 1
    assert len(resp.txn_groups[0].txn_results) == 2
