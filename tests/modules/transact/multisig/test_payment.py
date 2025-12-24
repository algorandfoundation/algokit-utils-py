from tests.modules.transact.conftest import TestDataLookup
from tests.modules.transact.transaction_asserts import assert_multisig_example


def test_multisig_example(test_data_lookup: TestDataLookup) -> None:
    """A human-readable example of forming a transaction and signing it with a multisignature sig"""
    vector = test_data_lookup("simplePayment")
    assert_multisig_example("payment", vector)
