# ruff: noqa: N999
"""
Example: Ed25519 Signing From Keyring

This example demonstrates how to retrieve secrets from a keyring and use them to sign
transactions.

Key concepts:
- Using keyring library to securely store and retrieve mnemonic
- Mock keyring for CI/testing when OS keyring is unavailable
- Implementing WrappedEd25519Seed interface for secure key handling
- Converting mnemonic to seed and deriving signing key
- Creating Algorand account with generated signers
- Registering signer with AlgorandClient using set_signer_from_account()
- Signing and sending a payment transaction

Prerequisites:
- LocalNet running (via `algokit localnet start`)
- OS that has keyring support (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- keyring library installed (uv pip install keyring)
- For testing without keyring: Mock keyring will be used automatically in CI
"""

import base64
import secrets

from shared.mock_keyring import get_keyring, KeyringProtocol
from shared import print_header, print_info, print_step, print_success

from algokit_algo25 import mnemonic_from_seed, seed_from_mnemonic
from algokit_crypto import WrappedEd25519Seed, ed25519_signing_key_from_wrapped_secret
from algokit_transact import generate_address_with_signers
from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams

MNEMONIC_NAME = "algorand-mainnet-mnemonic"


class KeyringWrappedSeed(WrappedEd25519Seed):
    """Implementation of WrappedEd25519Seed using OS keyring."""

    def __init__(self, service_name: str, account_name: str, keyring_instance: KeyringProtocol) -> None:
        self._service = service_name
        self._account = account_name
        self._keyring = keyring_instance

    def unwrap_ed25519_seed(self) -> bytearray:
        """Retrieve mnemonic from keyring and convert to seed."""
        mnemonic = self._keyring.get_password(self._service, self._account)
        if mnemonic is None:
            raise ValueError(f"No mnemonic found in keyring for {self._account}")
        return bytearray(seed_from_mnemonic(mnemonic))

    def wrap_ed25519_seed(self) -> None:
        """Re-wrap the seed after use (no-op for keyring)."""
        # Keyring handles persistence; nothing to wrap


def setup_keyring_secret(keyring_instance: KeyringProtocol) -> None:
    """Setup: Generate a random seed, create mnemonic, and store in keyring."""
    print_step(1, "Setup: Generate seed and store in keyring")

    # Generate a random 32-byte seed
    seed = secrets.token_bytes(32)
    print_info(f"Generated seed: {base64.b64encode(seed).decode()[:20]}...")

    # Convert seed to mnemonic
    mnemonic = mnemonic_from_seed(seed)
    print_info(f"Generated mnemonic: {' '.join(mnemonic.split()[:3])}...")

    # Store in keyring
    keyring_instance.set_password("algorand", MNEMONIC_NAME, mnemonic)
    print_info(f"Stored mnemonic in keyring (service='algorand', account='{MNEMONIC_NAME}')")


def main() -> None:
    print_header("Ed25519 Signing From Keyring Example")

    # Get appropriate keyring (real or mock)
    keyring_instance = get_keyring()
    if hasattr(keyring_instance, '__class__') and keyring_instance.__class__.__name__ == 'MockKeyring':
        print_info("WARNING: Using mock keyring for CI. Not secure - testing only!")

    # Setup: Create and store the secret
    setup_keyring_secret(keyring_instance)

    # Step 2: Create wrapped seed instance
    print_step(2, "Create wrapped seed implementation")

    wrapped_seed = KeyringWrappedSeed("algorand", MNEMONIC_NAME, keyring_instance)
    print_info("Created KeyringWrappedSeed instance")

    # Step 3: Derive signing key from wrapped secret
    print_step(3, "Derive signing key from wrapped secret")

    signing_key = ed25519_signing_key_from_wrapped_secret(wrapped_seed)
    print_info(f"Public key: {base64.b64encode(signing_key['ed25519_pubkey']).decode()[:20]}...")

    # Step 4: Create Algorand account with signers
    print_step(4, "Generate Algorand address with signers")

    algorand_account = generate_address_with_signers(
        signing_key["ed25519_pubkey"],
        signing_key["raw_ed25519_signer"],
    )
    print_info(f"Algorand address: {algorand_account.addr}")

    # Step 5: Connect to LocalNet and fund account
    print_step(5, "Connect to LocalNet and fund account")

    algorand = AlgorandClient.default_localnet()
    print_info("Connected to LocalNet")

    algorand.account.ensure_funded_from_environment(algorand_account.addr, AlgoAmount.from_algo(1))
    print_info("Account funded with 1 ALGO")

    # Step 6: Register signer with AlgorandClient
    print_step(6, "Register signer with AlgorandClient")

    algorand.set_signer_from_account(algorand_account)
    print_info("Signer registered for address")

    # Step 7: Sign and send payment transaction
    print_step(7, "Sign and send payment transaction")

    pay = algorand.send.payment(
        PaymentParams(
            sender=algorand_account.addr,
            receiver=algorand_account.addr,
            amount=AlgoAmount.from_micro_algo(0),
        )
    )
    print_info(f"Transaction ID: {pay.tx_ids[0]}")
    print_info(f"Confirmed in round: {pay.confirmation.confirmed_round}")

    print_success("Ed25519 signing from keyring example completed successfully!")


if __name__ == "__main__":
    main()
