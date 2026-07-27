"""Demonstrates the ``AlgorandClient`` facade — the central entry point of algokit-utils.

This maps to the Concepts -> Algorand Client docs page and shows how to
instantiate a client, reach the underlying SDK clients, configure signers, send
a transaction, and tune the suggested-params cache.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.algorand_client``.
"""

from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams
from examples._helpers import setup_localnet_environment


def main() -> None:
    env = setup_localnet_environment()
    account_a = env.account_a
    account_b = env.account_b

    # example: INSTANTIATE_ALGORAND_CLIENT
    algorand_client = AlgorandClient.default_localnet()
    # Other options include:
    # algorand_client = AlgorandClient.testnet()
    # algorand_client = AlgorandClient.mainnet()
    # algorand_client = AlgorandClient.from_environment()
    # example: INSTANTIATE_ALGORAND_CLIENT

    # example: SDK_CLIENTS
    algod = algorand_client.client.algod
    indexer = algorand_client.client.indexer
    kmd = algorand_client.client.kmd
    # example: SDK_CLIENTS
    assert algod is not None
    _ = (indexer, kmd)  # only shown, not used

    balance_before = algorand_client.account.get_information(account_b.address).amount

    # example: TXN_WITHOUT_SIGNER_CACHE
    algorand_client.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount(algo=1),
            signer=account_a.signer,
        )
    )
    # example: TXN_WITHOUT_SIGNER_CACHE

    # example: SIGNER_CONFIG
    algorand_client.set_default_signer(account_a.signer)
    algorand_client.set_signer(account_a.address, account_a.signer)
    algorand_client.set_signer_from_account(account_a)
    algorand_client.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount(algo=1),
            note=b"signed with the default signer",
        )
    )
    # example: SIGNER_CONFIG

    balance_after = algorand_client.account.get_information(account_b.address).amount
    assert balance_after.micro_algo == balance_before.micro_algo + AlgoAmount(algo=2).micro_algo

    # example: SUGGESTED_PARAMS_CONFIG
    algorand_client.set_default_validity_window(1000)
    suggested_params = algorand_client.get_suggested_params()
    algorand_client.set_suggested_params_cache(suggested_params)
    algorand_client.set_suggested_params_cache_timeout(0)
    # example: SUGGESTED_PARAMS_CONFIG
    assert suggested_params is not None

    print(f"Sent 2 ALGO to {account_b.address}")
    print(f"Balance went from {balance_before.algo} to {balance_after.algo} ALGO")


if __name__ == "__main__":
    main()
