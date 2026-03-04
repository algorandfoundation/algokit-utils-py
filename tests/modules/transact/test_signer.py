"""Tests for the signer module with ed25519 crypto integration.

These tests match the TypeScript implementation from algokit-transact,
testing the integration between the signer module and crypto module.
"""

import nacl.signing
import pytest

from algokit_crypto import (
    ed25519_generator,
    ed25519_verifier,
    peikert_hd_wallet_generator,
    pynacl_ed25519_generator,
    pynacl_ed25519_verifier,
)
from algokit_transact import (
    PaymentTransactionFields,
    Transaction,
    TransactionType,
    decode_signed_transaction,
    encode_transaction,
    generate_address_with_signers,
)
from algokit_transact.logicsig import LogicSig
from algokit_transact.logicsig import LogicSigAccount
from algokit_transact.signer import AddressWithSigners

# Sample LogicSig program (just some bytes)
LSIG_PROGRAM = bytes([1, 2, 3, 4, 5])


def _create_payment_transaction(sender: str) -> Transaction:
    """Create a simple payment transaction for testing."""
    return Transaction(
        transaction_type=TransactionType.Payment,
        sender=sender,
        first_valid=1,
        last_valid=1000,
        payment=PaymentTransactionFields(
            amount=1000,
            receiver="XBYLS2E6YI6XXL5BWCAMOA4GTWHXWENZMX5UHXMRNWWUQ7BXCY5WC5TEPA",
        ),
    )


def _run_tests(
    address_with_signers: AddressWithSigners,
    expected_pubkey: bytes,
) -> None:
    """Run common tests on an AddressWithSigners instance.

    Args:
        address_with_signers: An AddressWithSigners instance with all signing capabilities.
        expected_pubkey: The expected ed25519 public key bytes.
    """
    # Extract signer capabilities
    addr = address_with_signers.addr
    signer = address_with_signers.signer
    delegated_lsig_signer = address_with_signers.delegated_lsig_signer
    program_data_signer = address_with_signers.program_data_signer
    mx_bytes_signer = address_with_signers.mx_bytes_signer

    # Verify the address is derived from the expected public key
    from algokit_common import public_key_from_address

    assert public_key_from_address(addr) == expected_pubkey

    # Test that default verifier is the same object as the pynacl verifier
    assert ed25519_verifier is pynacl_ed25519_verifier

    # Create a LogicSig and transaction
    lsig = LogicSig(logic=LSIG_PROGRAM)
    txn = _create_payment_transaction(lsig.address)

    # Test 1: Transaction signing and verification
    stxns = signer([txn], [0])
    stxn = decode_signed_transaction(stxns[0])
    assert stxn.sig is not None
    # Verify the signature against the transaction bytes
    txn_bytes = encode_transaction(txn)
    assert ed25519_verifier(stxn.sig, txn_bytes, expected_pubkey) is True

    # Test 2: LogicSig delegation signing and verification
    lsig_account = LogicSigAccount(logic=lsig.logic, args=lsig.args, _address=addr)
    lsig_result = delegated_lsig_signer(lsig_account, None)
    assert lsig_result.sig is not None
    # Verify the delegation signature
    delegation_bytes = lsig.bytes_to_sign_for_delegation(None)
    assert ed25519_verifier(lsig_result.sig, delegation_bytes, expected_pubkey) is True

    # Test 3: Program data signing and verification
    program_data = bytes([10, 20, 30])
    program_data_sig = program_data_signer(lsig, program_data)
    # Verify the program data signature
    program_data_bytes = lsig.program_data_to_sign(program_data)
    assert ed25519_verifier(program_data_sig, program_data_bytes, expected_pubkey) is True

    # Test 4: MX bytes signing and verification
    mx_bytes = bytes([5, 4, 3, 2, 1])
    mx_bytes_sig = mx_bytes_signer(mx_bytes)
    # Verify the MX bytes signature
    mx_bytes_to_sign = b"MX" + mx_bytes
    assert ed25519_verifier(mx_bytes_sig, mx_bytes_to_sign, expected_pubkey) is True


class TestSigner:
    """Test suite for signer functionality with different ed25519 implementations."""

    def test_generate_signers_with_nacl(self) -> None:
        """Test generate_address_with_signers using PyNaCl (equivalent to tweetnacl)."""
        # Generate keypair using PyNaCl
        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key
        public_key = bytes(verify_key)

        # Create raw signer function
        def raw_signer(bytes_to_sign: bytes) -> bytes:
            signed = signing_key.sign(bytes_to_sign)
            return signed.signature

        # Generate address with signers
        address_with_signers = generate_address_with_signers(
            ed25519_pubkey=public_key,
            raw_ed25519_signer=raw_signer,
        )

        _run_tests(address_with_signers, public_key)

    def test_generate_signers_with_pynacl_ed25519_generator(self) -> None:
        """Test generate_address_with_signers using pynacl_ed25519_generator."""
        # Test that default generator is the same object as the pynacl generator
        assert ed25519_generator is pynacl_ed25519_generator

        # Generate keypair using pynacl generator
        generated = ed25519_generator()
        public_key = generated["ed25519_pubkey"]
        raw_signer = generated["raw_ed25519_signer"]

        # Generate address with signers
        address_with_signers = generate_address_with_signers(
            ed25519_pubkey=public_key,
            raw_ed25519_signer=raw_signer,
        )

        _run_tests(address_with_signers, public_key)

    def test_generate_signers_with_seed(self) -> None:
        """Test generate_address_with_signers using pynacl_ed25519_generator with seed."""
        # Use a deterministic seed
        seed = bytes([i % 256 for i in range(32)])

        # Generate keypair using pynacl generator with seed
        generated = pynacl_ed25519_generator(seed)
        public_key = generated["ed25519_pubkey"]
        raw_signer = generated["raw_ed25519_signer"]

        # Generate address with signers
        address_with_signers = generate_address_with_signers(
            ed25519_pubkey=public_key,
            raw_ed25519_signer=raw_signer,
        )

        _run_tests(address_with_signers, public_key)

        # Verify deterministic generation - same seed should produce same key
        generated2 = pynacl_ed25519_generator(seed)
        assert generated2["ed25519_pubkey"] == public_key

    def test_mx_bytes_full_flow(self) -> None:
        """Test full MX bytes signing flow with ed25519 generator."""
        # Generate a new keypair
        generated = ed25519_generator()
        public_key = generated["ed25519_pubkey"]

        # Generate Algorand-specific signing functions
        address_with_signers = generate_address_with_signers(
            ed25519_pubkey=public_key,
            raw_ed25519_signer=generated["raw_ed25519_signer"],
        )

        message = b"Hello, Algorand!"

        # Sign the message using MX bytes signer
        mx_bytes_sig = address_with_signers.mx_bytes_signer(message)

        # Get the bytes that were actually signed (MX domain separator + message)
        signed_bytes = b"MX" + message

        # Verify the signature
        is_valid = ed25519_verifier(mx_bytes_sig, signed_bytes, public_key)
        assert is_valid is True

        # Demonstrate it is not a raw signature (direct message signing would fail)
        is_raw_valid = ed25519_verifier(mx_bytes_sig, message, public_key)
        assert is_raw_valid is False

    def test_verifier_aliases(self) -> None:
        """Test that verifier aliases point to the same function."""
        assert ed25519_verifier is pynacl_ed25519_verifier

    def test_generator_aliases(self) -> None:
        """Test that generator aliases point to the same function."""
        assert ed25519_generator is pynacl_ed25519_generator

    def test_seed_size_validation(self) -> None:
        """Test that seed must be exactly 32 bytes."""
        # Valid seed size
        valid_seed = bytes(32)
        result = pynacl_ed25519_generator(valid_seed)
        assert "ed25519_pubkey" in result
        assert "ed25519_secret_key" in result
        assert "raw_ed25519_signer" in result

        # Invalid seed sizes
        with pytest.raises(ValueError, match="32 bytes"):
            pynacl_ed25519_generator(bytes(31))

        with pytest.raises(ValueError, match="32 bytes"):
            pynacl_ed25519_generator(bytes(33))

    def test_random_generation(self) -> None:
        """Test that random key generation produces different keys each time."""
        generated1 = ed25519_generator()
        generated2 = ed25519_generator()

        # Keys should be different (statistically almost certain)
        assert generated1["ed25519_pubkey"] != generated2["ed25519_pubkey"]
        assert generated1["ed25519_secret_key"] != generated2["ed25519_secret_key"]

    def test_generate_signers_with_peikert_hd_wallet_generator(self) -> None:
        """Test generate_address_with_signers using peikert_hd_wallet_generator."""
        # Generate HD wallet with account generator
        wallet_result = peikert_hd_wallet_generator()
        account_generator = wallet_result["account_generator"]

        # Generate an account at BIP44 path m/44'/283'/0'/0/0
        generated = account_generator(0, 0)
        public_key = generated["ed25519_pubkey"]
        raw_signer = generated["raw_ed25519_signer"]

        # Generate address with signers
        address_with_signers = generate_address_with_signers(
            ed25519_pubkey=public_key,
            raw_ed25519_signer=raw_signer,
        )

        _run_tests(address_with_signers, public_key)

    def test_full_xhd_mx_bytes_flow(self) -> None:
        """Test full xHD MX bytes signing flow with peikert_hd_wallet_generator."""
        # Generate a new wallet with rootkey and account generator
        wallet_result = peikert_hd_wallet_generator()
        account_generator = wallet_result["account_generator"]

        # Generate an account at BIP44 path m/44'/283'/0'/0/0
        generated = account_generator(0, 0)
        public_key = generated["ed25519_pubkey"]

        # Generate Algorand-specific signing functions
        address_with_signers = generate_address_with_signers(
            ed25519_pubkey=public_key,
            raw_ed25519_signer=generated["raw_ed25519_signer"],
        )

        message = b"Hello, Algorand!"

        # Sign the message
        mx_bytes_sig = address_with_signers.mx_bytes_signer(message)

        # Get the bytes that were actually signed (MX domain separator + message)
        signed_bytes = b"MX" + message

        # Verify the signature
        is_valid = ed25519_verifier(mx_bytes_sig, signed_bytes, public_key)
        assert is_valid is True

        # Demonstrate it is not a raw signature
        is_raw_valid = ed25519_verifier(mx_bytes_sig, message, public_key)
        assert is_raw_valid is False
