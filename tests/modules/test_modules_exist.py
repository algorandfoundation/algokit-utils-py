import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "algokit_transact",
        "algokit_common",
        "algokit_abi",
        "algokit_algod_client",
        "algokit_kmd_client",
        "algokit_indexer_client",
    ],
)
def test_transact_module_exists(module_name: str) -> None:
    module = __import__(module_name)
    assert module, "module should exist"
