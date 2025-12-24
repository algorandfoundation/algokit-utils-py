import pytest

from algokit_algod_client import AlgodClient
from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import SignTxnRequest
from algokit_transact import PaymentTransactionFields, Transaction, TransactionType, encode_transaction_raw

from .fixtures import TEST_WALLET_PASSWORD, generate_test_key

# Polytest Suite: POST v1_transaction_sign

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(
    localnet_kmd_client: KmdClient,
    localnet_algod_client: AlgodClient,
    wallet_handle: tuple[str, str, str],
) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    wallet_handle_token, _, _ = wallet_handle

    # Generate a key
    address = generate_test_key(localnet_kmd_client, wallet_handle_token)

    # Get suggested params from algod
    suggested_params = localnet_algod_client.suggested_params()

    # Create a simple payment transaction
    transaction = Transaction(
        transaction_type=TransactionType.Payment,
        sender=address,
        first_valid=suggested_params.first_valid,
        last_valid=suggested_params.last_valid,
        genesis_hash=suggested_params.genesis_hash,
        genesis_id=suggested_params.genesis_id,
        payment=PaymentTransactionFields(
            receiver=address,  # Self-payment
            amount=0,
        ),
    )

    # Encode the transaction
    transaction_bytes = encode_transaction_raw(transaction)

    # Sign the transaction
    result = localnet_kmd_client.sign_transaction(
        SignTxnRequest(
            wallet_handle_token=wallet_handle_token,
            transaction=transaction_bytes,
            wallet_password=TEST_WALLET_PASSWORD,
        )
    )

    assert result.signed_transaction is not None
