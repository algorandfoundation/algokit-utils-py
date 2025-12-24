from algokit_transact import PaymentTransactionFields, validate_transaction
from tests.modules.transact._validation import clone_transaction
from tests.modules.transact.conftest import TestDataLookup


def test_should_validate_valid_payment_transaction(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("simplePayment")
    tx = clone_transaction(
        vector.transaction,
        payment=PaymentTransactionFields(
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_payment_transaction_with_zero_amount(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("simplePayment")
    tx = clone_transaction(
        vector.transaction,
        payment=PaymentTransactionFields(
            amount=0,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_payment_transaction_with_close_remainder(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("simplePayment")
    tx = clone_transaction(
        vector.transaction,
        payment=PaymentTransactionFields(
            amount=1000,
            receiver="ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
            close_remainder_to="BNSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",
        ),
    )

    validate_transaction(tx)


def test_should_validate_self_payment_transaction(test_data_lookup: TestDataLookup) -> None:
    vector = test_data_lookup("simplePayment")
    sender = vector.transaction.sender
    tx = clone_transaction(
        vector.transaction,
        payment=PaymentTransactionFields(
            amount=1000,
            receiver=sender,
        ),
    )

    validate_transaction(tx)
