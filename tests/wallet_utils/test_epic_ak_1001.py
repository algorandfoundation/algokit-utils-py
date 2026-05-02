"""Tests for Epic AK-1001: Payments and transactions."""

import pytest
from algokit_utils import AlgoAmount, AlgorandClient
from algokit_utils.transactions.transaction_composer import TransactionComposer
from algokit_utils.transactions.types import (
    AssetCreateParams,
    AssetOptInParams,
    AssetTransferParams,
    PaymentParams,
)

from tests.wallet_utils.common import (
    balance,
    create_multisig_account,
    derive_hd_accounts_from_mnemonic,
    get_account_assets,
    get_asset_balance,
    get_asset_info,
)


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


class TestEpicAK1001:
    """Epic AK-1001: Payments and transactions."""

    def test_ak_995_split_funds(self, algorand: AlgorandClient) -> None:
        """
        AK-995: Split funds.
        As a user I would like to split my funds over various accounts without having to remember additional mnemonics.
        
        Acceptance Criteria:
        - Given I have derived 20 addresses
        - Then I can send funds to one of those addresses
        - And the wallet will keep track of those funds
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]
        
        algorand.account.ensure_funded_from_environment(
            sender.addr, AlgoAmount.from_micro_algo(1_000_000)
        )

        algorand.send.payment(
            PaymentParams(
                sender=sender.addr,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(500_000),
            )
        )
        
        # Sender balance: 1_000_000 - 500_000 - fee (1000) + 100_000 (initial funding) 
        # Wait, actually sender gets 100k from funding, sends 500k, pays 1000 fee
        # So remaining: 100_000 + 1_000_000 - 500_000 - 1000 = 599_000
        # The TS test expects 600_000 - 1000 which implies initial balance was 100_000
        assert balance(algorand, sender) == 600_000 - 1000
        assert balance(algorand, receiver) == 500_000

    def test_ak_1010_make_payment(self, algorand: AlgorandClient) -> None:
        """
        AK-1010: Make payment.
        As a user I want to make a payment to so I can pay my dues.
        
        Acceptance Criteria:
        - Given I have created addresses
        - And I know the balance
        - Then I can create a well formed Algo transaction
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]
        
        algorand.account.ensure_funded_from_environment(
            sender.addr, AlgoAmount.from_micro_algo(1_000_000)
        )

        algorand.send.payment(
            PaymentParams(
                sender=sender.addr,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(500_000),
            )
        )
        
        assert balance(algorand, sender) == 600_000 - 1000
        assert balance(algorand, receiver) == 500_000

    def test_ak_1011_make_complex_payment(self, algorand: AlgorandClient) -> None:
        """
        AK-1011: Make complex payment.
        As a user I want to send numerous interdependent transaction so that I can reduce costs and add business logic.
        
        Acceptance Criteria:
        - Given I have created my wallet
        - And I know my balance
        - Then I can create a sequence of well formed transactions with various assets and outputs
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        sender, recipient1, recipient2 = accounts[0], accounts[1], accounts[2]

        algorand.account.ensure_funded_from_environment(
            sender.addr, AlgoAmount.from_micro_algo(2_000_000)
        )

        asset_result = algorand.send.asset_create(
            AssetCreateParams(
                sender=sender.addr,
                total=1_000_000,
                decimals=2,
                asset_name="Complex ASA",
                unit_name="CASA",
            )
        )
        asset_id = asset_result.confirmation.asset_id
        assert asset_id is not None

        for recipient in [recipient1, recipient2]:
            algorand.account.ensure_funded_from_environment(
                recipient.addr, AlgoAmount.from_micro_algo(500_000)
            )

        result = (
            algorand.new_group()
            .add_payment(
                PaymentParams(
                    sender=sender.addr,
                    receiver=recipient2.addr,
                    amount=AlgoAmount.from_micro_algo(100_000),
                )
            )
            .add_asset_opt_in(
                AssetOptInParams(
                    sender=recipient1.addr,
                    asset_id=asset_id,
                )
            )
            .add_asset_transfer(
                AssetTransferParams(
                    sender=sender.addr,
                    receiver=recipient1.addr,
                    asset_id=asset_id,
                    amount=500,
                )
            )
            .send()
        )

        assert len(result.confirmations) == 3
        assert all(c.confirmed_round is not None for c in result.confirmations)

        # recipient2 got 100_000 from payment, plus 100_000 from funding, minus fees
        assert balance(algorand, recipient2) == 600_000 + 100_000  # Should be 700_000 before fees
        assert get_asset_balance(algorand, recipient1, asset_id) == 500

    def test_ak_1012_make_multisig_payment(self, algorand: AlgorandClient) -> None:
        """
        AK-1012: Make multi-sig payment.
        As a user I want to create and co-sign a payment for n people, so we can pay out dues.
        
        Acceptance Criteria:
        - Given I have created a multisig-address
        - And I know the balance
        - Then I can create a well formed transaction
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        account1, account2, receiver = accounts[0], accounts[1], accounts[2]

        algorand.account.ensure_funded_from_environment(
            account1.addr, AlgoAmount.from_micro_algo(1_000_000)
        )

        multisig = create_multisig_account([account1, account2], threshold=1, sub_signers=[account1], algorand=algorand)

        # Fund the multisig account
        algorand.send.payment(
            PaymentParams(
                sender=account1.addr,
                receiver=multisig.addr,
                amount=AlgoAmount.from_micro_algo(500_000),
            )
        )

        # Send from multisig to receiver
        algorand.send.payment(
            PaymentParams(
                sender=multisig.addr,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(200_000),
            )
        )

        assert balance(algorand, receiver) == 200_000

    def test_ak_1013_send_asa(self, algorand: AlgorandClient) -> None:
        """
        AK-1013: Send ASA.
        As a user I want to send one or more native assets to people so I can pay my dues.
        
        Acceptance Criteria:
        - Given I have created addresses
        - And I know the balance
        - Then I can create a well formed ASA transaction
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]

        algorand.account.ensure_funded_from_environment(
            sender.addr, AlgoAmount.from_micro_algo(2_000_000)
        )

        asset_result = algorand.send.asset_create(
            AssetCreateParams(
                sender=sender.addr,
                total=1_000_000,
                decimals=2,
                asset_name="Test ASA",
                unit_name="TASA",
                url="https://example.com/asa",
            )
        )
        asset_id = asset_result.confirmation.asset_id
        assert asset_id is not None

        algorand.account.ensure_funded_from_environment(
            receiver.addr, AlgoAmount.from_micro_algo(500_000)
        )
        
        algorand.send.asset_opt_in(
            AssetOptInParams(
                sender=receiver.addr,
                asset_id=asset_id,
            )
        )

        algorand.send.asset_transfer(
            AssetTransferParams(
                sender=sender.addr,
                receiver=receiver.addr,
                asset_id=asset_id,
                amount=500,
            )
        )

        assert get_asset_balance(algorand, receiver, asset_id) == 500
        assert get_asset_balance(algorand, sender, asset_id) == 1_000_000 - 500

    @pytest.mark.skip(reason="ARC20/ARC84 not yet implemented")
    def test_ak_1014_send_smart_contract_asset(self, algorand: AlgorandClient) -> None:
        """
        AK-1014: Send smart contract asset.
        As a user I want to be able to send ARC20 tokens to people so that I can pay my dues.
        
        Acceptance Criteria:
        - Given I have created addresses
        - And I know the balance
        - Then I can create a well formed ARC20 transaction
        
        Note: ARC20 → ARC84 (skipped as per TS implementation)
        """
        raise NotImplementedError("TEST NOT IMPLEMENTED")

    def test_ak_1015_send_nft(self, algorand: AlgorandClient) -> None:
        """
        AK-1015: Send NFT.
        As a user I want to be able to send ARC NFT tokens to people so that I can pay my dues.
        
        Acceptance Criteria:
        - Given I have created addresses
        - And I know the balance
        - Then I can create a well formed NFT transaction
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]

        algorand.account.ensure_funded_from_environment(
            sender.addr, AlgoAmount.from_micro_algo(2_000_000)
        )

        hash_val = bytes([1] * 32)
        asset_result = algorand.send.asset_create(
            AssetCreateParams(
                sender=sender.addr,
                total=1,
                decimals=0,
                asset_name="Test NFT",
                unit_name="TNFT",
                url="https://example.com/nft/1",
                metadata_hash=hash_val,
            )
        )
        asset_id = asset_result.confirmation.asset_id
        assert asset_id is not None

        algorand.account.ensure_funded_from_environment(
            receiver.addr, AlgoAmount.from_micro_algo(500_000)
        )
        
        algorand.send.asset_opt_in(
            AssetOptInParams(
                sender=receiver.addr,
                asset_id=asset_id,
            )
        )

        algorand.send.asset_transfer(
            AssetTransferParams(
                sender=sender.addr,
                receiver=receiver.addr,
                asset_id=asset_id,
                amount=1,
            )
        )

        assets = get_account_assets(algorand, receiver)
        nft_assets = []
        for holding in assets:
            if holding.amount == 0:
                continue
            asset_info = get_asset_info(algorand, holding.asset_id)
            if asset_info.total == 1 and asset_info.decimals == 0:
                nft_assets.append(asset_info)

        assert len(nft_assets) == 1
        assert nft_assets[0].asset_name == "Test NFT"
        assert nft_assets[0].url == "https://example.com/nft/1"
        assert nft_assets[0].metadata_hash == hash_val

    def test_ak_1016_add_metadata(self, algorand: AlgorandClient) -> None:
        """
        AK-1016: Add Metadata.
        As a user I want to add Metadata to my payments so that I can append information (encrypted or not).
        
        Acceptance Criteria:
        - Given I have a well formed transaction
        - Then I can add metadata to that transactions of free form
        - in ARC2 form
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]

        algorand.account.ensure_funded_from_environment(
            sender.addr, AlgoAmount.from_micro_algo(1_000_000)
        )
        algorand.account.ensure_funded_from_environment(
            receiver.addr, AlgoAmount.from_micro_algo(100_000)
        )

        note = TransactionComposer.arc2_note(
            {
                "dapp_name": "test-wallet",
                "format": "u",
                "data": "hello-world",
            }
        )

        result = algorand.send.payment(
            PaymentParams(
                sender=sender.addr,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(1),
                note=note,
            )
        )

        # Verify note is in transaction
        assert result.confirmation.txn.txn.note == note

    def test_ak_1017_transaction_costs(self, algorand: AlgorandClient) -> None:
        """
        AK-1017: Transaction costs.
        As a user I want to know what the cost is for executing the transaction so that I don't run into any surprises.
        
        Acceptance Criteria:
        - Given I have a well formed transaction
        - Then the SDK can tell me what the cost of executing this transaction will be
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        sender, receiver = accounts[0], accounts[1]

        txn = algorand.create_transaction.payment(
            PaymentParams(
                sender=sender.addr,
                receiver=receiver.addr,
                amount=AlgoAmount.from_micro_algo(1),
            )
        )

        assert txn.fee == 1000
