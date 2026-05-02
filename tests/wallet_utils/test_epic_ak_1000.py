"""Tests for Epic AK-1000: View wallet and balances."""

import dataclasses

import pytest
from algokit_utils import AlgoAmount, AlgorandClient
from algokit_utils.transactions.types import (
    AssetCreateParams,
    AssetOptInParams,
    AssetTransferParams,
    PaymentParams,
)

from tests.wallet_utils.common import (
    balance,
    derive_hd_accounts_from_mnemonic,
    get_account_assets,
    get_asset_balance,
    get_asset_info,
)


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


class TestEpicAK1000:
    """Epic AK-1000: View wallet, balances, and assets."""

    def test_ak_996_view_only_wallet(self, algorand: AlgorandClient) -> None:
        """
        AK-996: View only wallet.
        As a user I want to add a public address to my wallet to view it's balance (and make transactions).

        Acceptance Criteria:
        - Given I have a public key
        - or a batch of public keys
        - And track Balance
        - And construct unsigned transactions
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=1, algorand=algorand)
        account = accounts[0]

        algorand.account.ensure_funded_from_environment(
            account.addr, AlgoAmount.from_micro_algo(1_000_000)
        )

        # Should see 1_100_000 including the 100_000 initial funding
        assert balance(algorand, account) == 1_100_000

        # Can construct unsigned transactions (sender doesn't need signing)
        from algokit_utils.transactions.transaction_creator import AlgorandClientTransactionCreator as TransactionCreator
        pay_txn = algorand.create_transaction.payment(
            PaymentParams(
                sender=account.addr,
                receiver=account.addr,
                amount=AlgoAmount.from_micro_algo(1),
            )
        )
        assert pay_txn.sender == account.addr

    def test_ak_1006_current_balance(self, algorand: AlgorandClient) -> None:
        """
        AK-1006: Current balance.
        As a user I want to view my balance quickly so that I know how much algo I have.

        Acceptance Criteria:
        - Given I have created 20 addresses
        - Then I can see how much Algo I have on those addresses
        - And I can see how much Algo I have in my wallet
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        funded_indices = [0, 5, 10]
        amounts = [1_000_000, 500_000, 250_000]

        for i, idx in enumerate(funded_indices):
            algorand.account.ensure_funded_from_environment(
                accounts[idx].addr, AlgoAmount.from_micro_algo(amounts[i])
            )

        wallet_total = 0
        for account in accounts:
            account_balance = balance(algorand, account)
            wallet_total += account_balance

        for i, idx in enumerate(funded_indices):
            account_balance = balance(algorand, accounts[idx])
            assert account_balance >= amounts[i]

        for i in range(len(accounts)):
            if i not in funded_indices:
                assert balance(algorand, accounts[i]) == 0

        expected_total = sum(balance(algorand, a) for a in accounts)
        assert wallet_total == expected_total

    def test_ak_1007_current_asa_balance(self, algorand: AlgorandClient) -> None:
        """
        AK-1007: Current ASA balance.
        As a user I want to see my ASA balance quickly so I know what other currencies are in my wallet.

        Acceptance Criteria:
        - Given I have created 20 addresses
        - Then I can see how much ASA I have on those addresses
        - And I can see how much ASA I have in my wallet
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        creator = accounts[0]

        algorand.account.ensure_funded_from_environment(
            creator.addr, AlgoAmount.from_micro_algo(2_000_000)
        )

        asset_result = algorand.send.asset_create(
            AssetCreateParams(
                sender=creator.addr,
                total=1_000_000,
                decimals=2,
                asset_name="Test ASA",
                unit_name="TASA",
                url="https://example.com/asa",
            )
        )
        asset_id = asset_result.confirmation.asset_id
        assert asset_id is not None

        recipients = [accounts[1], accounts[2], accounts[3]]
        transfer_amounts = [100, 250, 500]

        for recipient in recipients:
            algorand.account.ensure_funded_from_environment(
                recipient.addr, AlgoAmount.from_micro_algo(500_000)
            )

        for recipient in recipients:
            algorand.send.asset_opt_in(
                AssetOptInParams(
                    sender=recipient.addr,
                    asset_id=asset_id,
                )
            )

        for i, recipient in enumerate(recipients):
            algorand.send.asset_transfer(
                AssetTransferParams(
                    sender=creator.addr,
                    receiver=recipient.addr,
                    asset_id=asset_id,
                    amount=transfer_amounts[i],
                )
            )

        wallet_total = 0
        for account in accounts:
            asset_balance = get_asset_balance(algorand, account, asset_id)
            wallet_total += asset_balance

        # Creator has initial minus transfers (with no clawback the decimals are handled differently)
        assert get_asset_balance(algorand, accounts[0], asset_id) == 1_000_000 - sum(transfer_amounts)
        assert get_asset_balance(algorand, accounts[1], asset_id) == 100
        assert get_asset_balance(algorand, accounts[2], asset_id) == 250
        assert get_asset_balance(algorand, accounts[3], asset_id) == 500
        for i in range(4, len(accounts)):
            assert get_asset_balance(algorand, accounts[i], asset_id) == 0

        assert wallet_total == 1_000_000

    def test_ak_1008_current_nft_balance(self, algorand: AlgorandClient) -> None:
        """
        AK-1008: Current NFT balance.
        As a user I want to see my NFTs quickly so I know what NFTS are in my wallet.

        Acceptance Criteria:
        - Given I have created 20 addresses
        - Then I can see how much NFTs I have on those addresses
        - And I can see how much NFT I have in my wallet
        - And its metadata
        """
        accounts = derive_hd_accounts_from_mnemonic(num_accounts=20, algorand=algorand)
        creator = accounts[0]

        algorand.account.ensure_funded_from_environment(
            creator.addr, AlgoAmount.from_micro_algo(2_000_000)
        )

        nfts = []
        for i in range(3):
            hash_val = bytes([i + 1] * 32)  # 32-byte metadata hash
            result = algorand.send.asset_create(
                AssetCreateParams(
                    sender=creator.addr,
                    total=1,
                    decimals=0,
                    asset_name=f"NFT {i + 1}",
                    unit_name=f"NFT{i + 1}",
                    url=f"https://example.com/nft/{i + 1}",
                    metadata_hash=hash_val,
                )
            )
            nfts.append({
                "asset_id": result.confirmation.asset_id,
                "asset_name": f"NFT {i + 1}",
                "url": f"https://example.com/nft/{i + 1}",
                "metadata_hash": hash_val,
            })

        recipients = [accounts[1], accounts[2], accounts[3]]
        for recipient in recipients:
            algorand.account.ensure_funded_from_environment(
                recipient.addr, AlgoAmount.from_micro_algo(500_000)
            )

        for i, recipient in enumerate(recipients):
            algorand.send.asset_opt_in(
                AssetOptInParams(
                    sender=recipient.addr,
                    asset_id=nfts[i]["asset_id"],
                )
            )

        for i, recipient in enumerate(recipients):
            algorand.send.asset_transfer(
                AssetTransferParams(
                    sender=creator.addr,
                    receiver=recipient.addr,
                    asset_id=nfts[i]["asset_id"],
                    amount=1,
                )
            )

        wallet_nft_total = 0
        for account in accounts:
            assets = get_account_assets(algorand, account)
            nft_holdings = []
            for holding in assets:
                print(f"DEBUG holding type: {type(holding)}, value: {holding}")
                if holding.amount == 0:
                    continue
                asset_info = get_asset_info(algorand, holding.asset_id)
                # NFT: total=1, decimals=0
                if asset_info.total == 1 and asset_info.decimals == 0:
                    nft_holdings.append({**dataclasses.asdict(holding), **asset_info.__dict__})

            if any(r.addr == account.addr for r in recipients):
                assert len(nft_holdings) == 1
                wallet_nft_total += 1
            else:
                assert len(nft_holdings) == 0

        assert wallet_nft_total == 3

        for i, recipient in enumerate(recipients):
            assets = get_account_assets(algorand, recipient)
            nft_assets = []
            for holding in assets:
                print(f"DEBUG holding type: {type(holding)}, value: {holding}")
                if holding.amount == 0:
                    continue
                asset_info = get_asset_info(algorand, holding.asset_id)
                if asset_info.total == 1 and asset_info.decimals == 0:
                    nft_assets.append(asset_info)

            assert len(nft_assets) == 1
            assert nft_assets[0].asset_name == nfts[i]["asset_name"]
            assert nft_assets[0].url == nfts[i]["url"]
            assert nft_assets[0].metadata_hash == nfts[i]["metadata_hash"]

    @pytest.mark.skip(reason="ARC20/ARC84 not yet implemented")
    def test_ak_1009_view_smart_contract_asset(self, algorand: AlgorandClient) -> None:
        """
        AK-1009: View smart contract asset.
        As a user I want to know how much ARC20 assets I have so I know what I have in my wallet.

        Acceptance Criteria:
        - Given I have created 20 addresses
        - Then I can see how much ARC20 I have on those addresses
        - And I can see how much ARC20 I have in my wallet

        Note: ARC20 → ARC84 (skipped as per TS implementation)
        """
        raise NotImplementedError("TEST NOT IMPLEMENTED")
