from pathlib import Path

import algosdk
import pytest
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import OnComplete, PaymentTxn

from algokit_utils import SigningAccount
from algokit_utils.algorand import AlgorandClient
from algokit_utils.applications.app_client import AppClient, AppClientMethodCallParams, FundAppAccountParams
from algokit_utils.applications.app_factory import AppFactoryCreateMethodCallParams
from algokit_utils.errors.logic_error import LogicError
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.transaction_composer import PaymentParams


@pytest.fixture
def algorand() -> AlgorandClient:
    return AlgorandClient.default_localnet()


@pytest.fixture
def funded_account(algorand: AlgorandClient) -> SigningAccount:
    new_account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()
    algorand.account.ensure_funded(new_account, dispenser, AlgoAmount.from_algo(100))
    return new_account


def load_arc32_spec(version: int) -> str:
    # Load the appropriate spec file from the resource-packer directory
    spec_path = Path(__file__).parent.parent / "artifacts" / "resource-packer" / f"ResourcePackerv{version}.arc32.json"
    return spec_path.read_text()


class BaseResourcePackerTest:
    """Base class for resource packing tests"""

    version: int

    @pytest.fixture(autouse=True)
    def setup(self, algorand: AlgorandClient, funded_account: SigningAccount) -> None:
        # Create app based on version
        spec = load_arc32_spec(self.version)
        factory = algorand.client.get_app_factory(
            app_spec=spec,
            default_sender=funded_account.address,
        )
        self.app_client, _ = factory.send.create(params=AppFactoryCreateMethodCallParams(method="createApplication"))
        self.app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_micro_algo(2334300)))
        self.app_client.send.call(
            AppClientMethodCallParams(method="bootstrap", static_fee=AlgoAmount.from_micro_algo(3_000))
        )

    @pytest.fixture
    def external_client(self, algorand: AlgorandClient, funded_account: SigningAccount) -> AppClient:
        external_spec = (
            Path(__file__).parent.parent / "artifacts" / "resource-packer" / "ExternalApp.arc32.json"
        ).read_text()
        return algorand.client.get_app_client_by_id(
            app_spec=external_spec,
            app_id=int(self.app_client.get_global_state()["externalAppID"].value),
            app_name="external",
            default_sender=funded_account.address,
        )

    def test_accounts_address_balance_invalid_ref(self, algorand: AlgorandClient) -> None:
        random_account = algorand.account.random()
        with pytest.raises(LogicError, match=f"unavailable Account {random_account.address}"):
            self.app_client.send.call(
                AppClientMethodCallParams(
                    method="addressBalance",
                    args=[random_account.address],
                ),
                send_params={
                    "populate_app_call_resources": False,
                },
            )

    def test_accounts_address_balance_valid_ref(self, algorand: AlgorandClient) -> None:
        random_account = algorand.account.random()
        self.app_client.send.call(
            AppClientMethodCallParams(
                method="addressBalance",
                args=[random_account.address],
            ),
        )

    def test_boxes_invalid_ref(self) -> None:
        with pytest.raises(LogicError, match="invalid Box reference"):
            self.app_client.send.call(
                AppClientMethodCallParams(
                    method="smallBox",
                ),
                send_params={
                    "populate_app_call_resources": False,
                },
            )

    def test_boxes_valid_ref(self) -> None:
        self.app_client.send.call(
            AppClientMethodCallParams(
                method="smallBox",
            ),
        )

        self.app_client.send.call(
            AppClientMethodCallParams(
                method="mediumBox",
            ),
        )

    def test_apps_external_unavailable_app(self) -> None:
        with pytest.raises(LogicError, match="unavailable App"):
            self.app_client.send.call(
                AppClientMethodCallParams(
                    method="externalAppCall",
                    static_fee=AlgoAmount.from_micro_algo(2_000),
                ),
                send_params={
                    "populate_app_call_resources": False,
                },
            )

    def test_apps_external_app(self) -> None:
        self.app_client.send.call(
            AppClientMethodCallParams(
                method="externalAppCall",
                static_fee=AlgoAmount.from_micro_algo(2_000),
            ),
        )

    def test_assets_unavailable_asset(self) -> None:
        with pytest.raises(LogicError, match="unavailable Asset"):
            self.app_client.send.call(
                AppClientMethodCallParams(
                    method="assetTotal",
                ),
                send_params={
                    "populate_app_call_resources": False,
                },
            )

    def test_assets_valid_asset(self) -> None:
        self.app_client.send.call(
            AppClientMethodCallParams(
                method="assetTotal",
            ),
        )

    def test_cross_product_reference_has_asset(self, funded_account: SigningAccount) -> None:
        self.app_client.send.call(
            AppClientMethodCallParams(
                method="hasAsset",
                args=[funded_account.address],
            ),
        )

    def test_cross_product_reference_invalid_external_local(self, funded_account: SigningAccount) -> None:
        with pytest.raises(LogicError, match="unavailable App"):
            self.app_client.send.call(
                AppClientMethodCallParams(
                    method="externalLocal",
                    args=[funded_account.address],
                ),
                send_params={
                    "populate_app_call_resources": False,
                },
            )

    def test_cross_product_reference_external_local(
        self, external_client: AppClient, funded_account: SigningAccount, algorand: AlgorandClient
    ) -> None:
        algorand.send.app_call_method_call(
            external_client.params.opt_in(
                AppClientMethodCallParams(
                    method="optInToApplication",
                    sender=funded_account.address,
                ),
            ),
        )

        algorand.send.app_call_method_call(
            self.app_client.params.call(
                AppClientMethodCallParams(
                    method="externalLocal",
                    args=[funded_account.address],
                    sender=funded_account.address,
                ),
            ),
        )

    def test_address_balance_invalid_account_reference(
        self,
    ) -> None:
        with pytest.raises(LogicError, match="unavailable Account"):
            self.app_client.send.call(
                AppClientMethodCallParams(
                    method="addressBalance",
                    args=[algosdk.account.generate_account()[1]],
                ),
                send_params={
                    "populate_app_call_resources": False,
                },
            )

    def test_address_balance(
        self,
    ) -> None:
        self.app_client.send.call(
            AppClientMethodCallParams(
                method="addressBalance",
                args=[algosdk.account.generate_account()[1]],
                on_complete=OnComplete.NoOpOC,
            ),
        )

    def test_cross_product_reference_invalid_has_asset(self, funded_account: SigningAccount) -> None:
        with pytest.raises(LogicError, match="unavailable Asset"):
            self.app_client.send.call(
                AppClientMethodCallParams(
                    method="hasAsset",
                    args=[funded_account.address],
                ),
                send_params={
                    "populate_app_call_resources": False,
                },
            )


class TestResourcePackerAVM8(BaseResourcePackerTest):
    """Test resource packing with AVM 8"""

    version = 8


class TestResourcePackerAVM9(BaseResourcePackerTest):
    """Test resource packing with AVM 9"""

    version = 9


class TestResourcePackerMixed:
    """Test resource packing with mixed AVM versions"""

    @pytest.fixture(autouse=True)
    def setup(self, algorand: AlgorandClient, funded_account: SigningAccount) -> None:
        # Create v8 app
        v8_spec = load_arc32_spec(8)
        v8_factory = algorand.client.get_app_factory(
            app_spec=v8_spec,
            default_sender=funded_account.address,
        )
        self.v8_client, _ = v8_factory.send.create(params=AppFactoryCreateMethodCallParams(method="createApplication"))

        # Create v9 app
        v9_spec = load_arc32_spec(9)
        v9_factory = algorand.client.get_app_factory(
            app_spec=v9_spec,
            default_sender=funded_account.address,
        )
        self.v9_client, _ = v9_factory.send.create(params=AppFactoryCreateMethodCallParams(method="createApplication"))

    def test_same_account(self, algorand: AlgorandClient, funded_account: SigningAccount) -> None:
        rekeyed_to = algorand.account.random()
        algorand.account.rekey_account(funded_account.address, rekeyed_to)

        random_account = algorand.account.random()

        txn_group = algorand.send.new_group()
        txn_group.add_app_call_method_call(
            self.v8_client.params.call(
                AppClientMethodCallParams(
                    method="addressBalance",
                    args=[random_account.address],
                    sender=funded_account.address,
                    signer=rekeyed_to.signer,
                ),
            ),
        )
        txn_group.add_app_call_method_call(
            self.v9_client.params.call(
                AppClientMethodCallParams(
                    method="addressBalance",
                    args=[random_account.address],
                    sender=funded_account.address,
                    signer=rekeyed_to.signer,
                )
            )
        )

        result = txn_group.send()

        v8_accounts = getattr(result.transactions[0].application_call, "accounts", None) or []
        v9_accounts = getattr(result.transactions[1].application_call, "accounts", None) or []
        assert len(v8_accounts) + len(v9_accounts) == 1

    def test_app_account(self, algorand: AlgorandClient, funded_account: SigningAccount) -> None:
        self.v8_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_micro_algo(328500)))
        self.v8_client.send.call(
            AppClientMethodCallParams(
                method="bootstrap",
                static_fee=AlgoAmount.from_micro_algo(3_000),
            ),
        )

        external_app_id = int(self.v8_client.get_global_state()["externalAppID"].value)
        external_app_addr = algosdk.logic.get_application_address(external_app_id)

        txn_group = algorand.send.new_group()
        txn_group.add_app_call_method_call(
            self.v8_client.params.call(
                AppClientMethodCallParams(
                    method="externalAppCall",
                    static_fee=AlgoAmount.from_micro_algo(2_000),
                    sender=funded_account.address,
                ),
            ),
        )
        txn_group.add_app_call_method_call(
            self.v9_client.params.call(
                AppClientMethodCallParams(
                    method="addressBalance",
                    args=[external_app_addr],
                    sender=funded_account.address,
                )
            )
        )

        result = txn_group.send()

        v8_apps = getattr(result.transactions[0].application_call, "foreign_apps", None) or []
        v9_accounts = getattr(result.transactions[1].application_call, "accounts", None) or []
        assert len(v8_apps) + len(v9_accounts) == 1


class TestResourcePackerMeta:
    """Test meta aspects of resource packing"""

    @pytest.fixture(autouse=True)
    def setup(self, algorand: AlgorandClient, funded_account: SigningAccount) -> None:
        external_spec = (
            Path(__file__).parent.parent / "artifacts" / "resource-packer" / "ExternalApp.arc32.json"
        ).read_text()
        factory = algorand.client.get_app_factory(
            app_spec=external_spec,
            default_sender=funded_account.address,
        )
        self.external_client, _ = factory.send.create(
            params=AppFactoryCreateMethodCallParams(method="createApplication")
        )

    def test_error_during_simulate(self) -> None:
        with pytest.raises(LogicError) as exc_info:
            self.external_client.send.call(
                AppClientMethodCallParams(
                    method="error",
                ),
            )
        assert "Error resolving execution info via simulate in transaction 0" in exc_info.value.logic_error_str

    def test_box_with_txn_arg(self, algorand: AlgorandClient, funded_account: SigningAccount) -> None:
        payment = PaymentTxn(
            sender=funded_account.address,
            receiver=funded_account.address,
            amt=0,
            sp=algorand.client.algod.suggested_params(),
        )
        payment_with_signer = TransactionWithSigner(payment, funded_account.signer)

        self.external_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_micro_algo(106100)))

        self.external_client.send.call(
            AppClientMethodCallParams(
                method="boxWithPayment",
                args=[payment_with_signer],
            ),
        )

    def test_sender_asset_holding(self) -> None:
        self.external_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_micro_algo(200_000)))

        self.external_client.send.call(
            AppClientMethodCallParams(
                method="createAsset",
                static_fee=AlgoAmount.from_micro_algo(2_000),
            ),
        )
        result = self.external_client.send.call(AppClientMethodCallParams(method="senderAssetBalance"))

        assert len(getattr(result.transaction.application_call, "accounts", None) or []) == 0

    def test_rekeyed_account(self, algorand: AlgorandClient, funded_account: SigningAccount) -> None:
        auth_addr = algorand.account.random()
        algorand.account.rekey_account(funded_account.address, auth_addr)

        self.external_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_micro_algo(200_001)))

        self.external_client.send.call(
            AppClientMethodCallParams(
                method="createAsset",
                static_fee=AlgoAmount.from_micro_algo(2_001),
            ),
        )
        result = self.external_client.send.call(AppClientMethodCallParams(method="senderAssetBalance"))

        assert len(getattr(result.transaction.application_call, "accounts", None) or []) == 0

    def test_create_box_in_new_app(self, algorand: AlgorandClient, funded_account: SigningAccount) -> None:
        self.external_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_micro_algo(200_000)))

        result = self.external_client.send.call(
            AppClientMethodCallParams(
                method="createBoxInNewApp",
                args=[
                    algorand.create_transaction.payment(
                        PaymentParams(
                            sender=funded_account.address,
                            receiver=self.external_client.app_address,
                            amount=AlgoAmount.from_algo(1),
                        )
                    )
                ],
                static_fee=AlgoAmount.from_micro_algo(4_000),
            ),
        )

        box_ref = result.transaction.application_call.boxes[0] if result.transaction.application_call.boxes else None
        assert box_ref is not None
        assert box_ref.app_index == 0  # type: ignore  # noqa: PGH003


def test_inner_txn_with_box(algorand: AlgorandClient, funded_account: SigningAccount) -> None:
    spec = (Path(__file__).parent.parent / "artifacts" / "testing_app_puya" / "app_spec.arc32.json").read_text()
    factory = algorand.client.get_app_factory(
        app_spec=spec,
        default_sender=funded_account.address,
    )
    app_client, _ = factory.send.bare.create()
    app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_algo(1)))
    result = app_client.send.call(
        AppClientMethodCallParams(method="bootstrap_external_app", static_fee=AlgoAmount.from_micro_algo(3_000))
    )
    external_app_id = result.abi_return
    assert isinstance(external_app_id, int), "expected app id"
    external_app = algorand.app.get_by_id(external_app_id)
    algorand.account.ensure_funded(
        external_app.app_address, funded_account, min_spending_balance=AlgoAmount.from_algo(1)
    )

    app_client.send.call(
        AppClientMethodCallParams(method="set_external_box", static_fee=AlgoAmount.from_micro_algo(2_000))
    )

    assert algorand.app.get_box_value(external_app_id, "box") == b"foo"
