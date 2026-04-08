import pytest

from algokit_kmd_client import KmdClient

from tests.fixtures.schemas.kmd import VersionsResponseSchema
from tests.modules.conftest import validate_with_schema

# Polytest Suite: GET versions

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(localnet_kmd_client: KmdClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    result = localnet_kmd_client.version()
    validate_with_schema(result, VersionsResponseSchema)

    assert result.versions is not None
