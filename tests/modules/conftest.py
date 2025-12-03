"""Shared test fixtures and utilities for module tests.

Mock server fixtures are in individual module conftest files:
- algod_client/conftest.py
- indexer_client/conftest.py
- kmd_client/conftest.py
"""

from dataclasses import fields, is_dataclass

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.json import JSONSnapshotExtension

from algokit_utils.algorand import AlgorandClient

# Test data constants matching TS mock server recordings
TEST_ADDRESS = "25M5BT2DMMED3V6CWDEYKSNEFGPXX4QBIINCOICLXXRU3UGTSGRMF3MTOE"
TEST_APP_ID = 718348254
TEST_APP_ID_WITH_BOXES = 742949200  # xgov testnet
TEST_BOX_NAME = "b64:cBbHBNV+zUy/Mz5IRhIrBLxr1on5wmidhXEavV+SasC8"
TEST_ASSET_ID = 705457144
TEST_TXID = "VIXTUMAPT7NR4RB2WVOGMETW4QY43KIDA3HWDWWXS3UEDKGTEECQ"
TEST_ROUND = 24099447


def _dataclass_to_dict(obj: object) -> object:
    """Recursively convert a dataclass to a dict for JSON serialization."""
    if obj is None:
        return None
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _dataclass_to_dict(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, bytes | bytearray | memoryview):
        return list(bytes(obj))
    if isinstance(obj, list | tuple):
        return [_dataclass_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    return obj


class DataclassSnapshotSerializer:
    """Serializer that converts dataclass models to JSON-serializable dicts."""

    @staticmethod
    def serialize(data: object) -> object:
        return _dataclass_to_dict(data)


@pytest.fixture
def snapshot_json(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Snapshot fixture configured for JSON output."""
    return snapshot.with_defaults(extension_class=JSONSnapshotExtension)


@pytest.fixture
def algorand_localnet() -> AlgorandClient:
    """AlgorandClient configured for localnet (real network, not mock)."""
    return AlgorandClient.default_localnet()
