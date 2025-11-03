from collections.abc import Iterable


def iter_app_call_vectors() -> Iterable[tuple[str, str]]:
    return (
        ("app call", "appCall"),
        ("app create", "appCreate"),
        ("app update", "appUpdate"),
        ("app delete", "appDelete"),
    )


def iter_asset_config_vectors() -> Iterable[tuple[str, str]]:
    return (
        ("asset create", "assetCreate"),
        ("asset config", "assetConfig"),
        ("asset destroy", "assetDestroy"),
    )


def iter_asset_transfer_vectors() -> Iterable[tuple[str, str]]:
    return (("asset opt-in", "optInAssetTransfer"),)


def iter_asset_freeze_vectors() -> Iterable[tuple[str, str]]:
    return (
        ("freeze", "assetFreeze"),
        ("unfreeze", "assetUnfreeze"),
    )


def iter_payment_vectors() -> Iterable[tuple[str, str]]:
    return (("payment", "simplePayment"),)


def iter_key_registration_vectors() -> Iterable[tuple[str, str]]:
    return (
        ("online key registration", "onlineKeyRegistration"),
        ("offline key registration", "offlineKeyRegistration"),
        ("non-participation key registration", "nonParticipationKeyRegistration"),
    )


def iter_heartbeat_vectors() -> Iterable[tuple[str, str]]:
    return (("heartbeat", "heartbeat"),)


def iter_state_proof_vectors() -> Iterable[tuple[str, str]]:
    return (("state proof", "stateProof"),)
