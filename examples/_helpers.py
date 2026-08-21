"""Shared setup for the runnable examples."""

from typing import NamedTuple

from algokit_utils import AlgoAmount, AlgorandClient, SigningAccount


class LocalNetEnvironment(NamedTuple):
    algorand: AlgorandClient
    account_a: SigningAccount
    account_b: SigningAccount


def setup_localnet_environment(initial_funds: AlgoAmount | None = None) -> LocalNetEnvironment:
    algorand = AlgorandClient.default_localnet()
    dispenser = algorand.account.localnet_dispenser()
    account_a = algorand.account.random()
    account_b = algorand.account.random()

    for account in (account_a, account_b):
        algorand.account.ensure_funded(
            account_to_fund=account.address,
            dispenser_account=dispenser.address,
            min_spending_balance=initial_funds or AlgoAmount.from_algo(10),
        )

    algorand.set_default_signer(account_a.signer)

    return LocalNetEnvironment(algorand=algorand, account_a=account_a, account_b=account_b)
