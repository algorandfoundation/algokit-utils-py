"""Demonstrates creating, funding, signing with and rekeying accounts via the AccountManager.

This maps to the Concepts -> Account management docs page and shows how to
create accounts (random, mnemonic, environment, KMD), fund them from a
dispenser, register and override signers, build a multisig account, and rekey
an account.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.accounts``.
"""

from typing import Any

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    MultisigMetadata,
    PaymentParams,
)

# A throwaway 25-word mnemonic used only to demonstrate account recovery.
# Never commit a real mnemonic to source control — load it from the
# environment or a secret store instead.
EXAMPLE_MNEMONIC = (
    "spider please secret fury picture gift grape lab result open dash race "
    "manual wreck knife wall pretty simple music power mom large private above basic"
)


def is_funded_dispenser(account: dict[str, Any]) -> bool:
    """Selects an online, well-funded KMD account, such as the default dispenser."""
    return account["status"] != "Offline" and account["amount"] > 1_000_000_000


def main() -> None:
    algorand = AlgorandClient.default_localnet()

    # example: ACCOUNT_MANAGER
    from algokit_utils import AccountManager

    account_manager = AccountManager(algorand.client)
    # example: ACCOUNT_MANAGER
    assert account_manager is not None

    # --- Create accounts ---

    # example: RANDOM_ACCOUNT
    random_account = algorand.account.random()
    # example: RANDOM_ACCOUNT

    # example: FROM_MNEMONIC
    mnemonic_account = algorand.account.from_mnemonic(mnemonic=EXAMPLE_MNEMONIC)
    # example: FROM_MNEMONIC

    # example: FROM_ENVIRONMENT
    # On LocalNet this idempotently creates and funds a KMD wallet named
    # "MY_ACCOUNT"; against TestNet/MainNet it loads MY_ACCOUNT_MNEMONIC from
    # the environment, so the same code runs everywhere.
    env_account = algorand.account.from_environment(
        name="MY_ACCOUNT", fund_with=AlgoAmount(algo=10)
    )
    # example: FROM_ENVIRONMENT

    # example: FROM_KMD
    kmd_account = algorand.account.from_kmd(name="MY_ACCOUNT")
    # example: FROM_KMD

    assert mnemonic_account.address
    assert env_account.address == kmd_account.address

    # --- KMD account management ---

    # example: KMD_ACCOUNT_MANAGER
    from algokit_utils import KmdAccountManager

    kmd_account_manager = KmdAccountManager(algorand.client)
    # example: KMD_ACCOUNT_MANAGER

    # example: KMD_MANAGER_METHODS
    # Load an account from a named wallet, filtering with a predicate
    dispenser_account = kmd_account_manager.get_wallet_account(
        "unencrypted-default-wallet", is_funded_dispenser
    )
    # A dedicated method for the default LocalNet dispenser
    localnet_dispenser_account = kmd_account_manager.get_localnet_dispenser_account()
    # Idempotently get-or-create a named account, funding it on creation
    created = kmd_account_manager.get_or_create_wallet_account("account1", AlgoAmount(algo=2))
    # example: KMD_MANAGER_METHODS
    assert dispenser_account is not None
    assert localnet_dispenser_account is not None
    assert created is not None

    # --- Fund accounts ---

    # example: DISPENSER
    # The pre-funded default LocalNet dispenser account
    localnet_dispenser = algorand.account.localnet_dispenser()
    # A dispenser configured via environment variables (falls back to LocalNet)
    dispenser = algorand.account.dispenser_from_environment()
    # example: DISPENSER
    assert dispenser is not None

    # example: ENSURE_FUNDED
    algorand.account.ensure_funded(
        account_to_fund=random_account.address,
        dispenser_account=localnet_dispenser.address,
        min_spending_balance=AlgoAmount(algo=10),
    )
    # example: ENSURE_FUNDED

    # example: ENSURE_FUNDED_FROM_ENVIRONMENT
    algorand.account.ensure_funded_from_environment(
        account_to_fund=random_account.address,
        min_spending_balance=AlgoAmount(algo=10),
    )
    # example: ENSURE_FUNDED_FROM_ENVIRONMENT

    # Accounts used by the signing, multisig and rekeying sections below.
    account_a = algorand.account.random()
    account_b = algorand.account.random()
    account_c = algorand.account.random()
    for account in (account_a, account_b, account_c):
        algorand.account.ensure_funded(
            account_to_fund=account.address,
            dispenser_account=localnet_dispenser.address,
            min_spending_balance=AlgoAmount(algo=10),
        )

    # --- Keys & signing ---

    # example: SET_DEFAULT_SIGNER
    algorand.account.set_default_signer(account_a.signer)
    # example: SET_DEFAULT_SIGNER

    # example: REGISTER_SIGNERS
    algorand.account.set_signer_from_account(account_a)
    algorand.account.set_signer_from_account(account_b)
    algorand.account.set_signer_from_account(account_c)
    # example: REGISTER_SIGNERS

    # example: GET_SIGNER
    signer = algorand.account.get_signer(account_a.address)
    # example: GET_SIGNER
    assert signer is not None

    # example: OVERRIDE_SIGNER
    # Build an unsigned transaction and pass the signer explicitly when adding
    # it to a group, overriding the signer registered for the sender.
    payment_txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount(algo=1),
            note=b"Payment from A to B",
        )
    )
    algorand.new_group().add_transaction(
        transaction=payment_txn, signer=account_a.signer
    ).send()
    # example: OVERRIDE_SIGNER

    # --- Multisig ---

    # example: MULTISIG
    # A 2-of-3 multisig account: any 2 of the 3 signers can authorise a transaction.
    multisig_account = algorand.account.multisig(
        metadata=MultisigMetadata(
            version=1,
            threshold=2,
            addresses=[
                account_a.address,
                account_b.address,
                account_c.address,
            ],
        ),
        signing_accounts=[account_a, account_b, account_c],
    )

    # A multisig account must be funded to initialise its state on the ledger
    algorand.account.ensure_funded(
        account_to_fund=multisig_account.address,
        dispenser_account=localnet_dispenser.address,
        min_spending_balance=AlgoAmount(algo=10),
    )

    # Send a payment from the multisig account. The required number of signatures
    # is collected automatically from the signing accounts provided above.
    algorand.send.payment(
        PaymentParams(
            sender=multisig_account.address,
            receiver=account_a.address,
            amount=AlgoAmount(algo=1),
        ),
    )
    # example: MULTISIG

    # --- Rekeying ---

    # example: REKEY_ACCOUNT
    # Rekey account_a so that account_b's key now authorises its transactions.
    # Passing a signing account for rekey_to registers it as account_a's signer.
    algorand.account.rekey_account(account=account_a.address, rekey_to=account_b)

    # account_a is still the sender, but account_b's key now signs automatically.
    result = algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount(algo=1),
        )
    )
    # example: REKEY_ACCOUNT

    print(f"Created and funded account {random_account.address}")
    print(f"Multisig account {multisig_account.address} sent a payment")
    print(f"Rekeyed account_a; payment confirmed in {result.tx_ids[0]}")


def testnet_dispenser_examples() -> None:
    """TestNet Dispenser API examples.

    These require TestNet and an ``ALGOKIT_DISPENSER_ACCESS_TOKEN``, so they are
    not run by the LocalNet test harness — ``main()`` never calls this function.
    They exist so the docs can render them as real, snippet-marked code.
    """
    algorand = AlgorandClient.testnet()
    random_account = algorand.account.random()

    # example: TESTNET_DISPENSER_ENSURE_FUNDED
    testnet_dispenser = algorand.client.get_testnet_dispenser()

    algorand.account.ensure_funded_from_testnet_dispenser_api(
        account_to_fund=random_account.address,
        dispenser_client=testnet_dispenser,
        min_spending_balance=AlgoAmount(algo=10),
    )
    # example: TESTNET_DISPENSER_ENSURE_FUNDED

    # example: TESTNET_DISPENSER_FUND
    testnet_dispenser.fund(address=random_account.address, amount=10)
    # example: TESTNET_DISPENSER_FUND


def kmd_wallet_admin_example() -> None:
    """Low-level KMD wallet administration.

    Creating and renaming wallets is rarely needed and not idempotent across
    runs, so this is not executed by the test harness — it backs the docs snippet.
    """
    algorand = AlgorandClient.default_localnet()

    # example: KMD_WALLET_ADMIN
    # Create a wallet, then rename it using the id returned on creation
    wallet = algorand.client.kmd.create_wallet(name="my-wallet", pswd="password")
    algorand.client.kmd.rename_wallet(
        id=wallet["wallet"]["id"],
        password="password",
        new_name="my-renamed-wallet",
    )
    # example: KMD_WALLET_ADMIN


def register_signer_variants_example() -> None:
    """Registering different underlying account types as signers.

    Uses illustrative signer objects, so it is not executed by the test harness —
    it backs the docs snippet.
    """
    from algokit_utils import (
        MultiSigAccount,
        SigningAccount,
        TransactionSignerAccount,
    )

    algorand = AlgorandClient.default_localnet()
    account_a = algorand.account.random()
    account_b = algorand.account.random()

    # example: SET_SIGNER_FROM_ACCOUNT_TYPES
    # set_signer_from_account accepts any underlying account type. For a logic
    # signature use algorand.account.logicsig(program, args); set_signer takes a
    # raw sender address and a TransactionSigner.
    (
        algorand.account.set_signer_from_account(
            TransactionSignerAccount(address=account_a.address, signer=account_a.signer)
        )
        .set_signer_from_account(SigningAccount(private_key=account_b.private_key))
        .set_signer_from_account(
            MultiSigAccount(
                MultisigMetadata(
                    version=1,
                    threshold=1,
                    addresses=[account_a.address, account_b.address],
                ),
                [account_a, account_b],
            )
        )
    )
    # example: SET_SIGNER_FROM_ACCOUNT_TYPES


if __name__ == "__main__":
    main()
