"""Demonstrates creating, funding and inspecting accounts with the AccountManager.

This maps to the Concepts -> Accounts docs page.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.accounts``.
"""

from algokit_utils import AlgoAmount, AlgorandClient


def main() -> None:
    algorand = AlgorandClient.default_localnet()
    dispenser = algorand.account.localnet_dispenser()

    # example: CREATE_AND_FUND_ACCOUNT
    account = algorand.account.random()
    algorand.account.ensure_funded(
        account_to_fund=account.address,
        dispenser_account=dispenser.address,
        min_spending_balance=AlgoAmount.from_algo(1),
    )
    info = algorand.account.get_information(account.address)
    # example: CREATE_AND_FUND_ACCOUNT

    assert info.amount.algo >= 1
    print(f"Account {account.address} funded with {info.amount.algo} ALGO")


if __name__ == "__main__":
    main()
