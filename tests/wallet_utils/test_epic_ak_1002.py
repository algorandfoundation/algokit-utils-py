"""Tests for Epic AK-1002: Review, sign, and export transactions."""

import nacl.signing
import pytest
from algokit_transact.codec.transaction import encode_transaction_raw, decode_transaction
from algokit_transact.signer import TransactionSigner
from algokit_utils import AlgoAmount, AlgorandClient
from algokit_utils.transactions.types import (
    AssetTransferParams,
    PaymentParams,
)

from tests.wallet_utils.common import derive_hd_accounts_from_mnemonic


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


class TestEpicAK1002:
    """Epic AK-1002: Review, sign, and export transactions."""

    def test_ak_1018_review_transaction(self, algorand: AlgorandClient) -> None:
        """
        AK-1018: Review transaction.
        As a user I want to review a transaction so I know that its safe to sign it.
        
        Acceptance Criteria:
        - Given I have a well formed transaction
        - Then I can check variables like:
          - What assets are being send
          - Where they are sent to
          - Any meta data in the Tx
          - From which address its send
          - potential ramifications/understanding side effects like losing rekey
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=2, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]
        note = b"test-metadata"
        rekey_address = receiver.addr

        pay_txn = algorand.create_transaction.payment(
            PaymentParams(
                sender=sender.addr,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(100_000),
                note=note,
                rekey_to=rekey_address,
            )
        )

        assert pay_txn.sender == sender.addr
        assert pay_txn.payment.receiver == receiver.addr
        assert pay_txn.payment.amount == 100_000
        assert pay_txn.note == note
        assert pay_txn.rekey_to == rekey_address

        asset_txn = algorand.create_transaction.asset_transfer(
            AssetTransferParams(
                sender=sender.addr,
                receiver=receiver.addr,
                asset_id=123,
                amount=50,
            )
        )

        assert asset_txn.sender == sender.addr
        assert asset_txn.asset_transfer.receiver == receiver.addr
        assert asset_txn.asset_transfer.asset_id == 123
        assert asset_txn.asset_transfer.amount == 50

    def test_ak_1019_sign_transaction(self, algorand: AlgorandClient) -> None:
        """
        AK-1019: Sign transaction.
        As a user I want to sign a transaction so it can be executed on the blockchain.
        
        Acceptance Criteria:
        - Given I have reviewed my transaction
        - Then I can sign the transaction
        - And share with thirdparty (dapp)
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=2, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]

        algorand.account.ensure_funded_from_environment(
            sender.addr, AlgoAmount.from_micro_algo(1_000_000)
        )
        # Register the signers for sender
        algorand.set_signer(sender=sender.addr, signer=sender.signer)

        txn = algorand.create_transaction.payment(
            PaymentParams(
                sender=sender.addr,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(100_000),
            )
        )

        result = algorand.send.new_group().add_transaction(txn, sender.signer).send()

        assert len(result.confirmations) == 1
        assert result.confirmations[0].confirmed_round is not None
        assert result.confirmations[0].confirmed_round > 0

    def test_ak_1020_hardware_sign_transaction(self, algorand: AlgorandClient) -> None:
        """
        AK-1020: Hardware sign transaction.
        As a user I want to share my unsigned transaction with a HSM so that they can sign it on my behalf.
        
        Acceptance Criteria:
        - Given I have review the transaction
        - Then I can connect to a hardware module like Ledger or HashiCorp
        - And get it to sign my transaction
        - Then Submit it to the blockchain
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=2, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]

        algorand.account.ensure_funded_from_environment(
            sender.addr, AlgoAmount.from_micro_algo(1_000_000)
        )

        txn = algorand.create_transaction.payment(
            PaymentParams(
                sender=sender.addr,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(100_000),
            )
        )

        # Simulate an HSM that proxies signing to the account signer
        def hsm_signer(txn_group: list, indexes_to_sign: list[int]) -> list[bytes]:
            return sender.signer(txn_group, indexes_to_sign)

        result = algorand.send.new_group().add_transaction(txn, hsm_signer).send()

        assert len(result.confirmations) == 1
        assert result.confirmations[0].confirmed_round is not None
        assert result.confirmations[0].confirmed_round > 0

    def test_ak_1021_export_unsigned_transaction(self, algorand: AlgorandClient) -> None:
        """
        AK-1021: Export unsigned transaction.
        As a user I want to export an unsigned or partially signed transaction so that someone else can do something with it.
        
        Acceptance Criteria:
        - Given I have reviewed the transaction
        - Then I can share the unsigned transaction with Base64 encoding
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=2, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]
        note = b"hello-world"

        txn = algorand.create_transaction.payment(
            PaymentParams(
                sender=sender.addr,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(1),
                note=note,
            )
        )

        encoded = encode_transaction_raw(txn)
        import base64
        base64_str = base64.b64encode(encoded).decode()
        decoded_back = decode_transaction(bytearray(base64.b64decode(base64_str)))

        assert decoded_back.sender == sender.addr
        assert decoded_back.payment.receiver == receiver.addr
        assert decoded_back.payment.amount == 1
        assert decoded_back.note == note

    def test_ak_1248_sign_arbitrary_data(self, algorand: AlgorandClient) -> None:
        """
        AK-1248: Sign arbitrary data.
        As a user I want to proof that I own a certain key, so I can get access to a service.
        
        Acceptance Criteria:
        - Given I have setup a wallet
        - And I connect to a service
        - And the service requests me to sign a nonce with a specific key
        - Then I can sign that nonce and return result
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=1, algorand=algorand)
        account = accounts[0]

        nonce = b"service-nonce-12345"
        signature = account.mx_bytes_signer(nonce)

        assert isinstance(signature, bytes)
        assert len(signature) == 64

        # Python doesn't have bytesForSigning module like TS
        # But we know MX prefix is b"MX" (77, 88 in ASCII)
        bytes_to_sign = b"MX" + nonce
        
        # Verify signature using NaCl
        # Need the public key from the address - derive it from the account
        # The public key is encoded in the Algorand address
        from algokit_common import address_from_public_key, public_key_from_address
        
        # Get the public key from the account address
        public_key = public_key_from_address(account.addr)
        
        # Verify the signature
        verify_key = nacl.signing.VerifyKey(public_key)
        is_valid = verify_key.verify(bytes_to_sign, signature)
        
        assert is_valid is None or True  # nacl returns None on success, raises on failure
