"""Unit tests for MultisigAccount class - mirrors multisig.spec.ts from algokit-utils-ts."""

import base64

import pytest
from algokit_common import public_key_from_address

from algokit_transact.multisig import MultisigAccount, MultisigMetadata
from algokit_transact.signing.types import MultisigSignature


class TestMultisigAccountCreateMultisigSignature:
    """Tests for MultisigAccount.create_multisig_signature()."""

    def test_should_create_empty_multisig_signature_with_correct_structure(self) -> None:
        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )
        multisig = msig_account.create_multisig_signature()

        assert multisig.version == 1
        assert multisig.threshold == 2
        assert len(multisig.subsigs) == 2
        assert multisig.subsigs[0].public_key == public_key_from_address(addrs[0])
        assert multisig.subsigs[1].public_key == public_key_from_address(addrs[1])
        assert multisig.subsigs[0].sig is None
        assert multisig.subsigs[1].sig is None

    def test_should_handle_single_participant(self) -> None:
        addrs = ["RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q"]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=1, addrs=addrs),
            sub_signers=[],
        )
        multisig = msig_account.create_multisig_signature()

        assert multisig.version == 1
        assert multisig.threshold == 1
        assert len(multisig.subsigs) == 1
        assert multisig.subsigs[0].public_key == public_key_from_address(addrs[0])


class TestParticipantsFromMultisigSignature:
    """Tests for extracting participants from multisig signatures."""

    def test_should_extract_participants_from_multisig_signature(self) -> None:
        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )
        multisig = msig_account.create_multisig_signature()
        extracted_participants = [subsig.public_key for subsig in multisig.subsigs]

        expected = [public_key_from_address(addr) for addr in addrs]
        assert extracted_participants == expected

    def test_should_extract_participants_even_when_signatures_are_present(self) -> None:
        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )
        multisig = msig_account.create_multisig_signature()
        signature = bytes([42] * 64)  # Mock signature
        signed_multisig = msig_account.apply_signature(multisig, addrs[0], signature)

        extracted_participants = [subsig.public_key for subsig in signed_multisig.subsigs]

        expected = [public_key_from_address(addr) for addr in addrs]
        assert extracted_participants == expected


class TestMultisigAccountFromSignatureAddress:
    """Tests for MultisigAccount.from_signature() and address derivation."""

    def test_should_derive_multisig_address_matches_rust_reference(self) -> None:
        """Matches Rust reference implementation."""
        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )
        multisig = msig_account.create_multisig_signature()
        msig_account_from_sig = MultisigAccount.from_signature(multisig)

        assert msig_account_from_sig.addr == "TZ6HCOKXK54E2VRU523LBTDQMQNX7DXOWENPFNBXOEU3SMEWXYNCRJUTBU"

    def test_should_produce_different_addresses_for_different_participant_orders(self) -> None:
        addrs1 = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]
        addrs2 = [
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
        ]

        msig_account1 = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs1),
            sub_signers=[],
        )
        msig_account2 = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs2),
            sub_signers=[],
        )

        assert msig_account1.addr != msig_account2.addr

    def test_should_handle_large_version_and_threshold_values(self) -> None:
        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account_large = MultisigAccount(
            params=MultisigMetadata(version=254, threshold=2, addrs=addrs),
            sub_signers=[],
        )
        msig_account_small = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )

        assert msig_account_large.addr != msig_account_small.addr


class TestMultisigAccountApplySignature:
    """Tests for MultisigAccount.apply_signature()."""

    def test_should_apply_signature_to_participant(self) -> None:
        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )
        multisig = msig_account.create_multisig_signature()
        signature = bytes([42] * 64)

        signed_multisig = msig_account.apply_signature(multisig, addrs[0], signature)

        assert signed_multisig.version == multisig.version
        assert signed_multisig.threshold == multisig.threshold
        assert signed_multisig.subsigs[0].sig == signature
        assert signed_multisig.subsigs[1].sig is None

    def test_should_replace_existing_signature(self) -> None:
        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )
        multisig = msig_account.create_multisig_signature()
        signature1 = bytes([42] * 64)
        signature2 = bytes([84] * 64)

        # Apply first signature
        signed_multisig1 = msig_account.apply_signature(multisig, addrs[0], signature1)
        assert signed_multisig1.subsigs[0].sig == signature1

        # Replace with second signature
        signed_multisig2 = msig_account.apply_signature(signed_multisig1, addrs[0], signature2)
        assert signed_multisig2.subsigs[0].sig == signature2


class TestMergeMultisignaturesViaApplySignature:
    """Tests for merging multisignatures."""

    def test_should_merge_compatible_multisignatures_by_applying_signatures_individually(self) -> None:
        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )

        signature1 = bytes([11] * 64)
        signature2 = bytes([22] * 64)

        # Apply both signatures to the same multisig
        multisig = msig_account.create_multisig_signature()
        multisig = msig_account.apply_signature(multisig, addrs[0], signature1)
        multisig = msig_account.apply_signature(multisig, addrs[1], signature2)

        assert multisig.version == 1
        assert multisig.threshold == 2
        assert multisig.subsigs[0].sig == signature1
        assert multisig.subsigs[1].sig == signature2

    def test_should_throw_error_for_incompatible_versions(self) -> None:
        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account1 = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )
        msig_account2 = MultisigAccount(
            params=MultisigMetadata(version=2, threshold=2, addrs=addrs),
            sub_signers=[],
        )

        msig2 = msig_account2.create_multisig_signature()

        with pytest.raises(ValueError, match="Multisig signature parameters do not match"):
            msig_account1.apply_signature(msig2, addrs[0], bytes(64))


class TestDecodeMultisigSignature:
    """Tests for encoding/decoding MultisigSignature via msgpack."""

    def test_should_decode_encoded_multisig_signature(self) -> None:
        from algokit_transact.codec.msgpack import decode_msgpack, encode_msgpack
        from algokit_transact.codec.serde import from_wire, to_wire_canonical

        addrs = [
            "RIMARGKZU46OZ77OLPDHHPUJ7YBSHRTCYMQUC64KZCCMESQAFQMYU6SL2Q",
            "ALGOC4J2BCZ33TCKSSAMV5GAXQBMV3HDCHDBSPRBZRNSR7BM2FFDZRFGXA",
        ]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )
        empty_multisig = msig_account.create_multisig_signature()
        signature = bytes([42] * 64)
        signed_multisig = msig_account.apply_signature(empty_multisig, addrs[0], signature)

        # Encode and decode
        encoded = encode_msgpack(to_wire_canonical(signed_multisig))
        decoded = from_wire(MultisigSignature, decode_msgpack(encoded))

        assert decoded.version == empty_multisig.version
        assert decoded.threshold == empty_multisig.threshold
        assert len(decoded.subsigs) == len(empty_multisig.subsigs)
        assert decoded.subsigs[0].public_key == public_key_from_address(addrs[0])
        assert decoded.subsigs[1].public_key == public_key_from_address(addrs[1])
        assert decoded.subsigs[0].sig == signature
        assert decoded.subsigs[1].sig is None


class TestMultisigExample:
    """Real-world example test matching observed transaction patterns."""

    def test_should_create_multisig_matching_observed_transaction_pattern(self) -> None:
        addrs = [
            "AXJVIQR43APV5HZ6F3J4MYNYR3GRRFHU56WTRFLJXFNNUJHDAX5SCGF3SQ",
            "QKR2CYWG4MQQAYCAF4LQARVQLLUF2JIDQO42OQ5YN2E7CHTLDURSJGNQRU",
        ]

        msig_account = MultisigAccount(
            params=MultisigMetadata(version=1, threshold=2, addrs=addrs),
            sub_signers=[],
        )

        # Decode the known base64 signatures
        signature1 = base64.b64decode(
            "H0W1kLRR68uDwacLk0N7qPuvm4NP09AmiaG+X6HPdsZOCJ5YV5ytc+jCvonAEz2sg+0k388T9ZAbqSZGag93Cg=="
        )
        signature2 = base64.b64decode(
            "UzvbTgDEfdG6w/HzaiwMePmNLiIk5z+hK4EZoCLR9ghgYMxy0IdS7iTCvPVFmVTDYM+r/W8Lox+lE6m4N/OvCw=="
        )

        # Apply signatures
        multisig = msig_account.create_multisig_signature()
        multisig = msig_account.apply_signature(multisig, addrs[0], signature1)
        multisig = msig_account.apply_signature(multisig, addrs[1], signature2)

        assert multisig.version == 1
        assert multisig.threshold == 2
        assert len(multisig.subsigs) == 2
        assert multisig.subsigs[0].public_key == public_key_from_address(addrs[0])
        assert multisig.subsigs[1].public_key == public_key_from_address(addrs[1])
        assert multisig.subsigs[0].sig == signature1
        assert multisig.subsigs[1].sig == signature2
