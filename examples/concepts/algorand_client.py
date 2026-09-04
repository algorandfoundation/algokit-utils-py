"""Demonstrates the ``AlgorandClient`` facade — the central entry point of algokit-utils.

This maps to the Concepts -> Algorand Client docs page and shows how to
instantiate a client, send a transaction, configure signers, reach the
underlying SDK clients, and tune the suggested-params cache.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.algorand_client``.
"""

from algokit_utils import AlgoAmount, PaymentParams
from examples._helpers import setup_localnet_environment


def main() -> None:
    env = setup_localnet_environment()
    account_a = env.account_a
    account_b = env.account_b

    # example: INSTANTIATE_ALGORAND_CLIENT
    from algokit_utils import AlgorandClient

    algorand_client = AlgorandClient.default_localnet()
    # example: INSTANTIATE_ALGORAND_CLIENT

    balance_before = algorand_client.account.get_information(account_b.address).amount

    # example: SEND_PAYMENT
    # `send` builds, signs, submits, and waits for confirmation
    result = algorand_client.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount(algo=1),
            signer=account_a.signer,  # explicit, no signer is registered yet
        )
    )
    print(f"Sent payment: {result.tx_id}")
    # example: SEND_PAYMENT

    # example: SIGNER_CONFIG
    # Register signers once; transactions look them up by sender address
    algorand_client.set_signer(account_a.address, account_a.signer)
    # Fallback for senders with no registered signer
    algorand_client.set_default_signer(account_b.signer)

    algorand_client.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount(algo=1),
            note=b"signed by the registered signer",
        )
    )
    # example: SIGNER_CONFIG

    # example: SDK_CLIENTS
    algod = algorand_client.client.algod
    indexer = algorand_client.client.indexer
    kmd = algorand_client.client.kmd
    # example: SDK_CLIENTS
    assert algod is not None
    _ = (indexer, kmd)  # only shown, not used

    # example: SUGGESTED_PARAMS_CONFIG
    algorand_client.set_default_validity_window(1000)
    suggested_params = algorand_client.get_suggested_params()
    algorand_client.set_suggested_params_cache(suggested_params)
    algorand_client.set_suggested_params_cache_timeout(0)
    # example: SUGGESTED_PARAMS_CONFIG
    assert suggested_params is not None

    balance_after = algorand_client.account.get_information(account_b.address).amount
    assert balance_after.micro_algo == balance_before.micro_algo + AlgoAmount(algo=2).micro_algo

    print(f"Balance of {account_b.address} went from {balance_before.algo} to {balance_after.algo} ALGO")


if __name__ == "__main__":
    main()
