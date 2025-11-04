import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "algokit_abi",
    ],
)
def test_module_exists(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module, "module should exist"
