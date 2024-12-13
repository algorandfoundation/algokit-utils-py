from collections.abc import Generator
from pathlib import Path

import pytest

from algokit_utils import Account
from algokit_utils.applications.app_client import (
    AppClientMethodCallWithSendParams,
    FundAppAccountParams,
)
from algokit_utils.applications.app_factory import AppFactoryCreateMethodCallParams
from algokit_utils.clients.algorand_client import AlgorandClient
from algokit_utils.config import config
from algokit_utils.errors.logic_error import LogicError
from algokit_utils.models.amount import AlgoAmount


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_local_net()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> Account:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(new_account, dispenser, AlgoAmount.from_algos(100))
    return new_account


def load_arc32_spec(version: int) -> str:
    # Load the appropriate spec file from the resource-packer directory
    spec_path = Path(__file__).parent.parent / "artifacts" / "resource-packer" / f"ResourcePackerv{version}.arc32.json"
    return spec_path.read_text()


class TestResourcePackerAVM8:
    """Test resource packing with AVM 8"""

    @pytest.fixture(autouse=True)
    def setup(self, algorand: AlgorandClient, funded_account: Account) -> Generator[None, None, None]:
        config.configure(populate_app_call_resources=True)

        # Create v8 app
        v8_spec = load_arc32_spec(8)
        v8_factory = algorand.client.get_app_factory(
            app_spec=v8_spec,
            default_sender=funded_account.address,
        )
        self.v8_client, _ = v8_factory.send.create(params=AppFactoryCreateMethodCallParams(method="createApplication"))
        self.v8_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_micro_algo(2334300)))
        self.v8_client.send.call(
            AppClientMethodCallWithSendParams(method="bootstrap", static_fee=AlgoAmount.from_micro_algo(3_000))
        )

        yield

        config.configure(populate_app_call_resources=False)

    def test_accounts_address_balance_invalid_ref(self, algorand: AlgorandClient) -> None:
        random_account = algorand.account.random()
        with pytest.raises(LogicError, match=f"invalid Account reference {random_account.address}"):
            self.v8_client.send.call(
                AppClientMethodCallWithSendParams(
                    method="addressBalance",
                    args=[random_account.address],  # Use the address
                    populate_app_call_resources=False,
                )
            )

    def test_accounts_address_balance_valid_ref(self, algorand: AlgorandClient) -> None:
        random_account = algorand.account.random()
        self.v8_client.send.call(
            AppClientMethodCallWithSendParams(
                method="addressBalance",
                args=[random_account.address],  # Use the address
                populate_app_call_resources=True,
            )
        )

    def test_boxes_invalid_ref(self) -> None:
        with pytest.raises(LogicError, match="invalid Box reference"):
            self.v8_client.send.call(
                AppClientMethodCallWithSendParams(
                    method="smallBox",
                    populate_app_call_resources=False,
                )
            )

    def test_boxes_valid_ref(self) -> None:
        self.v8_client.send.call(
            AppClientMethodCallWithSendParams(
                method="smallBox",
                populate_app_call_resources=True,
            )
        )

        self.v8_client.send.call(
            AppClientMethodCallWithSendParams(
                method="mediumBox",
                populate_app_call_resources=True,
            )
        )

    def test_apps_external_unavailable_app(self) -> None:
        with pytest.raises(LogicError, match="unavailable App"):
            self.v8_client.send.call(
                AppClientMethodCallWithSendParams(
                    method="externalAppCall",
                    populate_app_call_resources=False,
                    static_fee=AlgoAmount.from_micro_algo(2_000),
                )
            )

    def test_apps_external_app(self) -> None:
        self.v8_client.send.call(
            AppClientMethodCallWithSendParams(
                method="externalAppCall",
                populate_app_call_resources=True,
                static_fee=AlgoAmount.from_micro_algo(2_000),
            )
        )

    def test_assets_unavailable_asset(self) -> None:
        with pytest.raises(LogicError, match="unavailable Asset"):
            self.v8_client.send.call(
                AppClientMethodCallWithSendParams(
                    method="assetTotal",
                    populate_app_call_resources=False,
                )
            )

    def test_assets_valid_asset(self) -> None:
        self.v8_client.send.call(
            AppClientMethodCallWithSendParams(
                method="assetTotal",
                populate_app_call_resources=True,
            )
        )

    def test_cross_product_reference_invalid_has_asset(self, funded_account: Account) -> None:
        with pytest.raises(LogicError, match="unavailable Asset"):
            self.v8_client.send.call(
                AppClientMethodCallWithSendParams(
                    method="hasAsset",
                    args=[funded_account.address],
                    populate_app_call_resources=False,
                )
            )

    def test_cross_product_reference_has_asset(self, funded_account: Account) -> None:
        self.v8_client.send.call(
            AppClientMethodCallWithSendParams(
                method="hasAsset",
                args=[funded_account.address],
                populate_app_call_resources=True,
            )
        )

    def test_cross_product_reference_invalid_external_local(self, funded_account: Account) -> None:
        with pytest.raises(LogicError, match="unavailable App"):
            self.v8_client.send.call(
                AppClientMethodCallWithSendParams(
                    method="externalLocal",
                    args=[funded_account.address],
                    populate_app_call_resources=False,
                )
            )
