import pytest

from tests.modules.transact._helpers import iter_app_call_test_data
from tests.modules.transact.conftest import TestDataLookup
from tests.modules.transact.transaction_asserts import assert_multisig_example


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_test_data()))
def test_multisig_example(label: str, key: str, test_data_lookup: TestDataLookup) -> None:
    """A human-readable example of forming a transaction and signing it with a multisignature sig"""
    assert_multisig_example(label, test_data_lookup(key))
