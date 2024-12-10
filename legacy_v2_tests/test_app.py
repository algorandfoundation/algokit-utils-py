import pytest

from algokit_utils import AppDeployMetaData


@pytest.mark.parametrize(
    "app_note_json",
    [
        b'ALGOKIT_DEPLOYER:j{"name":"VotingRoundApp","version":"1.0","deletable":true,"updatable":true}',
        b'ALGOKIT_DEPLOYER:j{"name":"VotingRoundApp","version":"1.0","deletable":true}',
    ],
)
def test_metadata_serialization(app_note_json: bytes) -> None:
    metadata = AppDeployMetaData.decode(app_note_json)
    assert metadata
