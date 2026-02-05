from typing import Literal

from algopy import (
    ARC4Contract,
    Account,
    Application,
    Asset,
    BoxMap,
    Bytes,
    arc4,
    log,
    op,
)


class ExternalAppPuya(ARC4Contract):
    """Simple external app for testing - has a dummy method."""

    @arc4.abimethod(create="require")
    def create_application(self) -> None:
        pass

    @arc4.abimethod
    def dummy(self) -> None:
        """Empty method used to fill transaction groups."""
        pass


class ResourcePackerPuya(ARC4Contract):
    """
    Contract for testing resource population determinism.
    References multiple accounts, assets, apps, and boxes.
    """

    def __init__(self) -> None:
        # Box storage for testing
        self.byte_boxes = BoxMap(arc4.UInt8, Bytes)

    @arc4.abimethod(create="require")
    def create_application(self) -> None:
        pass

    @arc4.abimethod
    def dummy(self) -> None:
        """Empty method used to fill transaction groups."""
        pass

    @arc4.abimethod
    def many_resources(
        self,
        accounts: arc4.StaticArray[arc4.Address, Literal[4]],
        assets: arc4.StaticArray[arc4.UInt64, Literal[4]],
        apps: arc4.StaticArray[arc4.UInt64, Literal[4]],
        boxes: arc4.StaticArray[arc4.UInt8, Literal[4]],
    ) -> None:
        """
        Method that references many external resources.
        Used to test that resource population order is deterministic.
        """
        # Reference all accounts by checking they are NOT in the ledger
        for addr_arc4 in accounts:
            addr = Account(addr_arc4.bytes)
            min_bal, exists = op.AcctParamsGet.acct_min_balance(addr)
            assert not exists, "account should not be in ledger"

            # Check account is not opted into any of the assets
            for asset_arc4 in assets:
                asset = Asset(asset_arc4.native)
                balance, is_opted_in = op.AssetHoldingGet.asset_balance(addr, asset)
                assert not is_opted_in, "account should not hold asset"

            # Check account is not opted into any of the apps
            for app_arc4 in apps:
                app = Application(app_arc4.native)
                assert not addr.is_opted_in(app), "account should not be opted into app"

        # Reference all assets by checking their total supply
        for asset_arc4 in assets:
            asset = Asset(asset_arc4.native)
            assert asset.total > 0, "asset must have total > 0"

        # Reference all apps by logging their creator
        for app_arc4 in apps:
            app = Application(app_arc4.native)
            log(app.creator)

        # Reference boxes by writing to them
        for box_key in boxes:
            self.byte_boxes[box_key] = Bytes(b"foo")