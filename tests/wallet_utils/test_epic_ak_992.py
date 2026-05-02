"""Tests for Epic AK-992: Wallet creation and recovery."""

import pytest
from algokit_transact import MultisigAccount, MultisigMetadata
from algokit_utils import AlgoAmount, AlgorandClient
from algokit_utils.transactions.types import PaymentParams

from tests.wallet_utils.common import (
    balance,
    create_multisig_account,
    derive_hd_accounts_from_bip39_mnemonic,
    derive_hd_accounts_from_mnemonic,
    generate_algo25_mnemonic,
    derive_hd_accounts_from_algo25_mnemonic,
)


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


class TestEpicAK992:
    """Epic AK-992: Wallet creation, recovery, and migration."""

    def test_ak_993_create_address_from_mnemonic(self, algorand: AlgorandClient) -> None:
        """
        AK-993: Create address.
        As a user I would like to create an address using 24 or 25 mnemonic words
        so that I can receive funds.
        
        Acceptance Criteria:
        - Given I have the SDK running
        - And I request a mnemonic
        - Then I can derive 20 addresses
        - And have the private public keys
        """
        # 24-word BIP39 mnemonic path
        from mnemonic import Mnemonic
        mnemo = Mnemonic("english")
        bip39_mnemonic = mnemo.generate(strength=256)
        bip39_accounts = derive_hd_accounts_from_bip39_mnemonic(bip39_mnemonic, 20, algorand)
        
        assert len(bip39_accounts) == 20
        for account in bip39_accounts:
            # Verify we have a valid address (58 characters)
            assert len(account.addr) == 58
            # Verify we can sign using mx_bytes_signer (64-byte signature)
            test_data = b"\x01"
            sig = account.mx_bytes_signer(test_data)
            assert len(sig) == 64

        # 25-word Algorand mnemonic path
        algo25_mnemonic = generate_algo25_mnemonic()
        algo25_accounts = derive_hd_accounts_from_algo25_mnemonic(algo25_mnemonic, 20, algorand)
        
        assert len(algo25_accounts) == 20
        for account in algo25_accounts:
            # Verify we have a valid address (58 characters)
            assert len(account.addr) == 58
            # Verify we can sign using mx_bytes_signer (64-byte signature)
            test_data = b"\x01"
            sig = account.mx_bytes_signer(test_data)
            assert len(sig) == 64

    def test_ak_994_recover_address(self, algorand: AlgorandClient) -> None:
        """
        AK-994: Recover address.
        As a user I would like to recover my 24 or 25 mnemonic words so I can see my funds.
        
        Acceptance Criteria:
        - Given I have the SDK running
        - And I have a mnemonic
        - Then I can derive 20 addresses
        - And have the public private keys
        """
        # 24-word BIP39 recover
        from mnemonic import Mnemonic
        mnemo = Mnemonic("english")
        bip39_mnemonic = mnemo.generate(strength=256)
        set1 = derive_hd_accounts_from_bip39_mnemonic(bip39_mnemonic, 20, algorand)
        set2 = derive_hd_accounts_from_bip39_mnemonic(bip39_mnemonic, 20, algorand)
        
        for i in range(20):
            assert set1[i].addr == set2[i].addr

        # 25-word Algorand recover
        algo25_mnemonic = generate_algo25_mnemonic()
        set3 = derive_hd_accounts_from_algo25_mnemonic(algo25_mnemonic, 20, algorand)
        set4 = derive_hd_accounts_from_algo25_mnemonic(algo25_mnemonic, 20, algorand)
        
        for i in range(20):
            assert set3[i].addr == set4[i].addr

    def test_ak_997_create_multisig(self, algorand: AlgorandClient) -> None:
        """
        AK-997: Create multi-sig.
        As a user I want to split the responsibility/security of my funds with other people
        so I can still recover it when I lose my mnemonic.
        
        Acceptance Criteria:
        - Given I have derived 20 addresses
        - And I have my co-signers n public keys
        - And I know the order
        - Then I can derive the multi-sig address
        - And track the address
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        cosigners = accounts[:2]
        addrs = [a.addr for a in cosigners]

        # Derive multisig address (threshold 1, 2 co-signers)
        msig = create_multisig_account(cosigners, threshold=1, algorand=algorand)

        # Track the address via algod - fund it
        algorand.account.ensure_funded_from_environment(
            msig.addr, AlgoAmount.from_micro_algo(1_000_000)
        )
        info = algorand.account.get_information(msig.addr)
        assert info.amount >= 1_000_000

        # Use it to send a payment
        tracked = algorand.account.multisig(
            MultisigMetadata(version=1, threshold=1, addrs=addrs),
            [cosigners[0]],
        )
        receiver = derive_hd_accounts_from_mnemonic(num_accounts=1, algorand=algorand)[0]
        
        algorand.send.payment(
            PaymentParams(
                sender=tracked,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(500_000),
            )
        )
        
        assert balance(algorand, receiver) == 500_000

    def test_ak_998_recover_multisig(self, algorand: AlgorandClient) -> None:
        """
        AK-998: Recover multi-sig.
        As a user I want to be able to recover my joined account so I can view my balance.
        
        Acceptance Criteria:
        - Given I have derived 20 addresses
        - And I have my co-signers n public keys
        - And I know the order
        - Then I can derive the multi-sig address
        - And track the address
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        cosigners = accounts[:2]
        addrs = [a.addr for a in cosigners]

        # Original
        original = create_multisig_account(cosigners, threshold=1, algorand=algorand)

        # Recover with same ordered public keys
        recovered = create_multisig_account(cosigners, threshold=1, algorand=algorand)
        assert recovered.addr == original.addr

        # Track and verify via algod - fund it
        algorand.account.ensure_funded_from_environment(
            recovered.addr, AlgoAmount.from_micro_algo(1_000_000)
        )
        info = algorand.account.get_information(recovered.addr)
        assert info.amount >= 1_000_000

    def test_ak_999_migrate_wallet(self, algorand: AlgorandClient) -> None:
        """
        AK-999: Migrate wallet.
        As a user I want to migrate from my single address 25 word to a multi-address 24 words wallet
        so I can split my funds.
        
        Acceptance Criteria:
        - Given I have a 25 word, single account
        - And I have a 24 word, multi account
        - Then I can move all my funds from my account to the second account
        """
        # 25-word single account
        single_account = algorand.account.from_mnemonic(mnemonic=generate_algo25_mnemonic())
        algorand.account.ensure_funded_from_environment(
            single_account.addr, AlgoAmount.from_micro_algo(1_000_000)
        )

        # 24-word multi-account
        from mnemonic import Mnemonic
        mnemo = Mnemonic("english")
        bip39_mnemonic = mnemo.generate(strength=256)
        multi_accounts = derive_hd_accounts_from_bip39_mnemonic(bip39_mnemonic, 20, algorand)
        destination = multi_accounts[0]

        # Migrate all funds using close_remainder_to
        algorand.send.payment(
            PaymentParams(
                sender=single_account,
                receiver=destination.addr,
                close_remainder_to=destination.addr,
                amount=AlgoAmount.from_micro_algo(0),
            )
        )

        assert balance(algorand, single_account.addr) == 0
        # Account should have received the funds minus fee
        assert balance(algorand, destination) >= 1_000_000 - 1000
