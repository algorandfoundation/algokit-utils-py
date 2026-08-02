"""Pure unit tests for app-id matching in AppClient error transformers (#296)."""

from algokit_utils.applications.app_client import _error_refers_to_app_id


def test_error_refers_to_exact_app_id() -> None:
    message = (
        "Network request error. Received status 400: "
        "TransactionPool.Remember: transaction ABC123: logic eval error: "
        "assert failed pc=42. Details: app=1142, pc=42"
    )
    assert _error_refers_to_app_id(message, 1142) is True


def test_error_does_not_match_prefix_app_id() -> None:
    """app=1142 must not match an error that refers to app=11423 (prefix collision)."""
    message = "transaction XYZ789: logic eval error: assert failed pc=10. Details: app=11423, pc=10"
    assert _error_refers_to_app_id(message, 1142) is False
    assert _error_refers_to_app_id(message, 11423) is True


def test_error_matches_app_id_at_end_of_string() -> None:
    assert _error_refers_to_app_id("failed for app=99", 99) is True
    assert _error_refers_to_app_id("failed for app=99", 9) is False


def test_error_matches_app_id_followed_by_non_digit() -> None:
    assert _error_refers_to_app_id("Details: app=42, pc=7", 42) is True
    assert _error_refers_to_app_id("Details: app=42; pc=7", 42) is True
    assert _error_refers_to_app_id("Details: app=42 pc=7", 42) is True


def test_error_without_app_id_does_not_match() -> None:
    assert _error_refers_to_app_id("logic eval error: assert failed pc=1", 1142) is False
    assert _error_refers_to_app_id("", 1) is False
