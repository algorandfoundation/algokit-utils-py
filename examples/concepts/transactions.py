"""Demonstrates sending a payment transaction and inspecting the result.

This maps to the Concepts -> Transactions docs page.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.transactions``.
"""

from algokit_utils import AlgoAmount, PaymentParams
from examples._helpers import setup_localnet_environment


def main() -> None:
    env = setup_localnet_environment()
    algorand, account_a, account_b = env

    balance_before = algorand.account.get_information(account_b.address).amount

    # example: SEND_PAYMENT
    result = algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
        )
    )
    print(f"Payment sent in transaction {result.tx_id}")
    # example: SEND_PAYMENT

    balance_after = algorand.account.get_information(account_b.address).amount
    assert balance_after.micro_algo == balance_before.micro_algo + AlgoAmount.from_algo(1).micro_algo


if __name__ == "__main__":
    main()
