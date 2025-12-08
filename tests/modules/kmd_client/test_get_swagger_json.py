import pytest

# Polytest Suite: GET swagger_json

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.skip(reason="No mock server recording available for this endpoint")
def test_basic_request_and_response_validation() -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    # Note: swagger.json endpoint is not typically part of the standard KMD API
