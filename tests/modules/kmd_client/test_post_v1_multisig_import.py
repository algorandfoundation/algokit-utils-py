import pytest

# Polytest Suite: POST v1_multisig_import

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.skip(reason="No mock server recording available for this endpoint - requires localnet test")
def test_basic_request_and_response_validation() -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    # Note: This endpoint requires a wallet handle token which requires stateful setup
