"""Tests for IdentifierSanitizer camelCase / PascalCase → snake_case conversion."""

import pytest

from oas_generator.naming import IdentifierSanitizer

_san = IdentifierSanitizer()


# ── snake() ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Simple camelCase
        ("makeHealthCheck", "make_health_check"),
        ("searchForAccounts", "search_for_accounts"),
        # Trailing acronym (e.g. "ByID")
        ("lookupAccountByID", "lookup_account_by_id"),
        ("lookupApplicationByID", "lookup_application_by_id"),
        ("lookupApplicationLogsByID", "lookup_application_logs_by_id"),
        # Acronym followed by PascalCase word — the original bug
        ("lookupApplicationBoxByIDAndName", "lookup_application_box_by_id_and_name"),
        # Multiple consecutive acronyms
        ("parseXMLToJSON", "parse_xml_to_json"),
        ("getHTTPSUrl", "get_https_url"),
        # Leading acronym
        ("HTMLParser", "html_parser"),
        ("JSONResponse", "json_response"),
        # Single word
        ("version", "version"),
        ("Version", "version"),
        # Already snake_case passthrough
        ("already_snake", "already_snake"),
        # Digits mixed in
        ("sha256Hash", "sha256_hash"),
        ("get2FACode", "get2_fa_code"),
        # Hyphenated / non-word chars
        ("content-type", "content_type"),
        ("X-Forwarded-For", "x_forwarded_for"),
        # Python reserved words get suffix
        ("class", "class_"),
        ("import", "import_"),
    ],
)
def test_snake(raw: str, expected: str) -> None:
    assert _san.snake(raw) == expected


# ── pascal() ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("make_health_check", "MakeHealthCheck"),
        ("lookupAccountByID", "LookupAccountById"),
        ("version", "Version"),
    ],
)
def test_pascal(raw: str, expected: str) -> None:
    assert _san.pascal(raw) == expected


# ── camel() ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("MakeHealthCheck", "makeHealthCheck"),
        ("Version", "version"),
    ],
)
def test_camel(raw: str, expected: str) -> None:
    assert _san.camel(raw) == expected
