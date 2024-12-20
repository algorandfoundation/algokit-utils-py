import warnings

warnings.warn(
    """The legacy v2 asset module is deprecated and will be removed in a future version.

Replacements for opt_in/opt_out functionality:

1. Using TransactionComposer:
   composer.add_asset_opt_in(AssetOptInParams(
       sender=account.address,
       asset_id=123
   ))
   composer.add_asset_opt_out(AssetOptOutParams(
       sender=account.address,
       asset_id=123,
       creator=creator_address
   ))

2. Using AlgorandClient:
   client.asset.opt_in(AssetOptInParams(...))
   client.asset.opt_out(AssetOptOutParams(...))

3. For bulk operations:
   client.asset.bulk_opt_in(account, [asset_ids])
   client.asset.bulk_opt_out(account, [asset_ids])

Refer to AssetManager class from algokit_utils for more functionality.""",
    DeprecationWarning,
    stacklevel=2,
)

from algokit_utils._legacy_v2.asset import *  # noqa: F403, E402
