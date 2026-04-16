# ruff: noqa: N999
"""
Example: HD Signing From Keyring

This example demonstrates how to retrieve HD extended private keys from a keyring and use
them to sign transactions.

Key concepts:
- Generating an HD wallet using the Peikert derivation scheme
- Deriving extended private keys (96 bytes: scalar + prefix + chain code)
- Storing and retrieving HD keys from OS keyring
- Mock keyring for CI/testing when OS keyring is unavailable
- Implementing WrappedHdExtendedPrivateKey interface
- The last 32 bytes (chain code) are not needed for signing
- Padding 64-byte secrets to 96 bytes for storage efficiency
- Registering signer with AlgorandClient using set_signer_from_account()

Prerequisites:
- LocalNet running (via `algokit localnet start`)
- OS that has keyring support (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- keyring library installed (uv pip install keyring)
- For testing without keyring: Mock keyring will be used automatically in CI
"""

import base64
import secrets

from shared import print_header, print_info, print_step, print_success
from shared.mock_keyring import KeyringProtocol, get_keyring

from algokit_crypto import (
    WrappedHdExtendedPrivateKey,
    ed25519_signing_key_from_wrapped_secret,
    peikert_hd_wallet_generator,
)
from algokit_transact import generate_address_with_signers
from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams

SECRET_NAME = "algorand-hd-extended-key"
# Extended private key is 96 bytes (32 scalar + 32 prefix + 32 chain code)
# We store only first 64 bytes since chain code not needed for signing
EXTENDED_PRIVATE_KEY_LENGTH = 96
STORED_KEY_LENGTH = 64


class KeyringWrappedHdKey(WrappedHdExtendedPrivateKey):
    """Implementation of WrappedHdExtendedPrivateKey using OS keyring.

    Note: We store only the first 64 bytes (scalar + prefix) in the keyring
    since the chain code is not needed for signing. The unwrap function pads
    it back to 96 bytes.
    """

    def __init__(self, service_name: str, account_name: str, keyring_instance: KeyringProtocol) -> None:
        self._service = service_name
        self._account = account_name
        self._keyring = keyring_instance

    def unwrap_hd_extended_private_key(self) -> bytearray:
        """Retrieve extended key from keyring and pad to 96 bytes if needed."""
        secret_b64 = self._keyring.get_password(self._service, self._account)
        if secret_b64 is None:
            raise ValueError(f"No HD key found in keyring for {self._account}")

        esk = bytearray(base64.b64decode(secret_b64))

        # The last 32 bytes of the extended private key is the chain code, which is not
        # needed for signing. This means in most cases you can just store the first 64
        # bytes and then pad the secret to 96 bytes in the unwrap function. If you are
        # storing the full 96 bytes, you can just return the secret as is.
        if len(esk) == STORED_KEY_LENGTH:
            padded = bytearray(96)
            padded[:64] = esk
            print_info("  (Padded 64-byte key to 96 bytes - chain code not needed for signing)")
            return padded

        return esk

    def wrap_hd_extended_private_key(self) -> None:
        """Re-wrap the extended key after use (no-op for keyring)."""
        # Keyring handles persistence; nothing to wrap


def setup_keyring_hd_secret(keyring_instance: KeyringProtocol) -> bytearray:
    """Setup: Generate HD wallet, derive extended private key, and store in keyring."""
    print_step(1, "Setup: Generate HD wallet and store extended key in keyring")

    # Generate a random 64-byte seed for HD wallet
    seed = secrets.token_bytes(64)
    print_info(f"Generated HD wallet seed: {base64.b64encode(seed).decode()[:20]}...")

    # Create HD wallet using Peikert derivation
    wallet = peikert_hd_wallet_generator(bytearray(seed))
    print_info("Created HD wallet with Peikert derivation scheme")

    # Derive account 0, index 0
    account_result = wallet["account_generator"](0, 0)
    esk = account_result["extended_private_key"]  # 96 bytes

    print_info(f"Extended private key length: {len(esk)} bytes")
    print_info("  - First 32 bytes: scalar (for signing)")
    print_info("  - Next 32 bytes: prefix (for nonce derivation)")
    print_info("  - Last 32 bytes: chain code (for key derivation, not needed for signing)")

    # Store only the first 64 bytes in keyring (chain code not needed for signing)
    esk_64 = bytes(esk[:64])
    esk_b64 = base64.b64encode(esk_64).decode()
    keyring_instance.set_password("algorand", SECRET_NAME, esk_b64)
    print_info(f"Stored first 64 bytes of extended key in keyring (service='algorand', account='{SECRET_NAME}')")

    return esk


def main() -> None:
    print_header("HD Signing From Keyring Example")

    # Get appropriate keyring (real or mock)
    keyring_instance = get_keyring()
    if hasattr(keyring_instance, '__class__') and keyring_instance.__class__.__name__ == 'MockKeyring':
        print_info("WARNING: Using mock keyring for CI. Not secure - testing only!")

    # Setup: Create and store the HD secret
    setup_keyring_hd_secret(keyring_instance)

    # Step 2: Create wrapped HD key instance
    print_step(2, "Create wrapped HD key implementation")

    wrapped_key = KeyringWrappedHdKey("algorand", SECRET_NAME, keyring_instance)
    print_info("Created KeyringWrappedHdKey instance")

    # Step 3: Derive signing key from wrapped secret
    print_step(3, "Derive signing key from wrapped HD secret")

    signing_key = ed25519_signing_key_from_wrapped_secret(wrapped_key)
    print_info(f"Public key: {base64.b64encode(signing_key['ed25519_pubkey']).decode()[:20]}...")

    # Step 4: Create Algorand account with signers
    print_step(4, "Generate Algorand address with signers")

    algorand_account = generate_address_with_signers(
        signing_key["ed25519_pubkey"],
        signing_key["raw_ed25519_signer"],
    )
    print_info(f"Algorand address: {algorand_account.addr}")

    # Verify the signing key was created successfully
    print_info("Derived signing key successfully from wrapped HD extended private key")

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

    print_success("HD signing from keyring example completed successfully!")


if __name__ == "__main__":
    main()
