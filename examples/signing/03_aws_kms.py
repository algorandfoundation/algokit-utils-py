# ruff: noqa: N999
"""
Example: Ed25519 Signing from AWS KMS

This example demonstrates how to use AWS KMS to perform Ed25519 signing for Algorand
transactions. Includes a mock KMS client for testing when AWS credentials are not available.

Key concepts:
- Using AWS KMS for secure key storage and signing
- Mock KMS client for local development/testing
- Retrieving public key from KMS in SPKI format
- Parsing DER-encoded public key to extract raw Ed25519 public key
- Implementing RawEd25519Signer with KMS
- Generating Algorand address from KMS-managed key
- Registering signer with AlgorandClient using set_signer_from_account()

Prerequisites:
- LocalNet running (via `algokit localnet start`)
- AWS credentials configured (for real KMS usage):
  - AWS_REGION environment variable
  - KEY_ID environment variable
  - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY (or use OIDC in CI)
- boto3 library installed (uv pip install boto3)
- For testing without AWS: Mock client will be used automatically
"""

import base64
import os
from pathlib import Path
from typing import Protocol

import nacl.signing
from dotenv import load_dotenv
from shared import print_header, print_info, print_step, print_success

from algokit_transact import generate_address_with_signers
from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams

# Load .env file
load_dotenv(Path(__file__).parent / ".env")

# Ed25519 SPKI prefix (DER-encoded SubjectPublicKeyInfo)
# 0x30 0x2a 0x30 0x05 0x06 0x03 0x2b 0x65 0x70 0x03 0x21 0x00
ED25519_SPKI_PREFIX = bytes([0x30, 0x2A, 0x30, 0x05, 0x06, 0x03, 0x2B, 0x65, 0x70, 0x03, 0x21, 0x00])
# SPKI format: 12-byte prefix + 32-byte Ed25519 public key
SPKI_PUBKEY_LENGTH = 44


class MockKMSClient:
    """Mock KMS client for local development/testing when AWS credentials are not available.

    This generates an in-memory keypair and simulates KMS signing operations.
    WARNING: This is not secure and should only be used for testing.
    """

    def __init__(self) -> None:
        print_info("WARNING: Using MockKMSClient with in-memory key pair. Not secure - testing only!")
        # Generate an ephemeral keypair for testing
        # In production, this would come from actual AWS KMS
        self._signing_key = nacl.signing.SigningKey.generate()
        self._verify_key = self._signing_key.verify_key

    def sign(self, *, KeyId: str, Message: bytes, MessageType: str, SigningAlgorithm: str) -> dict:  # noqa: N803, ARG002
        """Mock sign operation."""
        if not Message:
            raise ValueError("No message provided for signing")

        # Sign using PyNaCl (equivalent to Ed25519)
        signed = self._signing_key.sign(Message)
        return {"Signature": bytes(signed.signature), "SigningAlgorithm": "ED25519_SHA_512"}

    def get_public_key(self, *, KeyId: str) -> dict:  # noqa: N803, ARG002
        """Mock get_public_key operation."""
        # Create SPKI format public key (DER-encoded SubjectPublicKeyInfo)
        public_key_bytes = bytes(self._verify_key)
        spki_key = ED25519_SPKI_PREFIX + public_key_bytes
        return {"PublicKey": spki_key, "KeySpec": "ED25519"}


class KMSClient(Protocol):
    """Protocol for KMS client interface."""

    def sign(self, *, KeyId: str, Message: bytes, MessageType: str, SigningAlgorithm: str) -> dict: ...  # noqa: N803
    def get_public_key(self, *, KeyId: str) -> dict: ...  # noqa: N803


def get_kms_client() -> KMSClient:
    """Get KMS client - real if AWS_REGION is set, mock otherwise."""
    if os.environ.get("AWS_REGION"):
        # Use real AWS KMS
        import boto3

        region = os.environ.get("AWS_REGION")
        print_info(f"Using AWS KMS in region: {region}")
        return boto3.client("kms", region_name=region)
    else:
        # Use mock client for testing
        return MockKMSClient()


def extract_ed25519_pubkey(spki_pubkey: bytes) -> bytes:
    """Extract raw Ed25519 public key from SPKI format.

    Args:
        spki_pubkey: DER-encoded SubjectPublicKeyInfo

    Returns:
        32-byte Ed25519 public key

    Raises:
        ValueError: If the public key format is unexpected
    """
    if len(spki_pubkey) != SPKI_PUBKEY_LENGTH:  # 12-byte prefix + 32-byte key
        raise ValueError(f"Unexpected SPKI public key length: {len(spki_pubkey)} bytes (expected 44)")

    if not spki_pubkey.startswith(ED25519_SPKI_PREFIX):
        raise ValueError("Unexpected public key format - not Ed25519 SPKI")

    return spki_pubkey[12:44]  # Last 32 bytes are the raw Ed25519 public key


def main() -> None:
    print_header("AWS KMS Signing Example")

    # Step 1: Initialize KMS client
    print_step(1, "Initialize KMS client")

    kms = get_kms_client()
    key_id = os.environ.get("KEY_ID", "mock-key-id")
    print_info(f"Using Key ID: {key_id}")

    # Step 2: Get public key from KMS
    print_step(2, "Retrieve public key from KMS")

    pubkey_response = kms.get_public_key(KeyId=key_id)
    spki_pubkey = pubkey_response["PublicKey"]

    if isinstance(spki_pubkey, memoryview):
        spki_pubkey = bytes(spki_pubkey)

    print_info(f"Retrieved public key: {len(spki_pubkey)} bytes (SPKI format)")

    # Step 3: Extract raw Ed25519 public key
    print_step(3, "Extract raw Ed25519 public key from SPKI")

    ed25519_pubkey = extract_ed25519_pubkey(spki_pubkey)
    print_info(f"Extracted Ed25519 public key: {base64.b64encode(ed25519_pubkey).decode()[:20]}...")

    # Step 4: Create raw signer function
    print_step(4, "Create RawEd25519Signer using KMS")

    def raw_ed25519_signer(data: bytes) -> bytes:
        """Sign data using KMS."""
        response = kms.sign(
            KeyId=key_id,
            Message=data,
            MessageType="RAW",
            SigningAlgorithm="ED25519_SHA_512",
        )
        signature = response["Signature"]
        if signature is None:
            raise ValueError("No signature returned from KMS")
        if isinstance(signature, memoryview):
            return bytes(signature)
        return signature

    print_info("Created raw_ed25519_signer function")

    # Step 5: Generate Algorand address with signers
    print_step(5, "Generate Algorand address with KMS signers")

    algorand_account = generate_address_with_signers(ed25519_pubkey, raw_ed25519_signer)
    print_info(f"Algorand address: {algorand_account.addr}")

    # Step 6: Connect to LocalNet and fund account
    print_step(6, "Connect to LocalNet and fund account")

    algorand = AlgorandClient.default_localnet()
    print_info("Connected to LocalNet")

    algorand.account.ensure_funded_from_environment(algorand_account.addr, AlgoAmount.from_algo(1))
    print_info("Account funded with 1 ALGO")

    # Step 7: Register signer with AlgorandClient
    print_step(7, "Register signer with AlgorandClient")

    algorand.set_signer_from_account(algorand_account)
    print_info("Signer registered for address")

    # Step 8: Sign and send payment transaction
    print_step(8, "Sign and send payment transaction using KMS")

    pay = algorand.send.payment(
        PaymentParams(
            sender=algorand_account.addr,
            receiver=algorand_account.addr,
            amount=AlgoAmount.from_micro_algo(0),
        )
    )
    print_info(f"Transaction ID: {pay.tx_ids[0]}")
    print_info(f"Confirmed in round: {pay.confirmation.confirmed_round}")

    print_success("AWS KMS signing example completed successfully!")


if __name__ == "__main__":
    main()
