import base64
from typing import Any

from algosdk import encoding
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    AtomicTransactionComposerStatus,
    SimulateABIResult,
    SimulateAtomicTransactionResponse,
)
from algosdk.error import AtomicTransactionComposerError
from algosdk.v2client.algod import AlgodClient


def simulate_atc_315(atc: AtomicTransactionComposer, client: AlgodClient) -> SimulateAtomicTransactionResponse:
    """
    Ported from algosdk 2.1.2

    Send the transaction group to the `simulate` endpoint and wait for results.
    An error will be thrown if submission or execution fails.
    The composer's status must be SUBMITTED or lower before calling this method,
    since execution is only allowed once.

    Returns:
        SimulateAtomicTransactionResponse: Object with simulation results for this
            transaction group, a list of txIDs of the simulated transactions,
            an array of results for each method call transaction in this group.
            If a method has no return value (void), then the method results array
            will contain None for that method's return value.
    """

    if atc.status > AtomicTransactionComposerStatus.SUBMITTED:
        raise AtomicTransactionComposerError(  # type: ignore[no-untyped-call]
            "AtomicTransactionComposerStatus must be submitted or lower to simulate a group"
        )

    signed_txns = atc.gather_signatures()
    txn = b"".join(
        base64.b64decode(encoding.msgpack_encode(txn)) for txn in signed_txns  # type: ignore[no-untyped-call]
    )
    simulation_result = client.algod_request(
        "POST", "/transactions/simulate", data=txn, headers={"Content-Type": "application/x-binary"}
    )
    assert isinstance(simulation_result, dict)

    # Only take the first group in the simulate response
    txn_group: dict[str, Any] = simulation_result["txn-groups"][0]
    txn_results = txn_group["txn-results"]

    # Parse out abi results
    results = []
    for method_index, method in atc.method_dict.items():
        tx_info = txn_results[method_index]["txn-result"]

        result = atc.parse_result(method, atc.tx_ids[method_index], tx_info)
        sim_result = SimulateABIResult(
            tx_id=result.tx_id,
            raw_value=result.raw_value,
            return_value=result.return_value,
            decode_error=result.decode_error,
            tx_info=result.tx_info,
            method=result.method,
        )
        results.append(sim_result)

    return SimulateAtomicTransactionResponse(
        version=simulation_result.get("version", 0),
        failure_message=txn_group.get("failure-message", ""),
        failed_at=txn_group.get("failed-at"),
        simulate_response=simulation_result,
        tx_ids=atc.tx_ids,
        results=results,
    )
