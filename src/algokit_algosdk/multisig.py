import base64
from collections import OrderedDict
from typing import Sequence

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from . import constants, encoding, error

# Vendored from py-algorand-sdk/algosdk/transaction.py (multisig sections) under MIT License.

__all__ = ["Multisig", "MultisigSubsig"]


class Multisig:
    """
    Represents a multisig account and signatures.
    """

    def __init__(self, version: int, threshold: int, addresses: Sequence[str]) -> None:
        self.version = version
        self.threshold = threshold
        self.subsigs = [MultisigSubsig(encoding.decode_address(addr)) for addr in addresses]

    def validate(self) -> None:
        """Check if the multisig account is valid."""
        if self.version != 1:
            raise error.UnknownMsigVersionError

        if self.threshold <= 0 or not self.subsigs or self.threshold > len(self.subsigs):
            raise error.InvalidThresholdError

        if len(self.subsigs) > constants.multisig_account_limit:
            raise error.MultisigAccountSizeError

    def address_bytes(self) -> bytes:
        """Return the raw bytes of the multisig account address."""
        msig_bytes = (
            bytes(constants.msig_addr_prefix, "utf-8")
            + bytes([self.version])
            + bytes([self.threshold])
        )
        for subsig in self.subsigs:
            if isinstance(subsig.public_key, bytes):
                msig_bytes += subsig.public_key
            else:
                raise TypeError("expected public_key to be bytes")
        return encoding.checksum(msig_bytes)

    def address(self) -> str:
        """Return the multisig account address."""
        encoded = encoding.encode_address(self.address_bytes())
        assert isinstance(encoded, str)
        return encoded

    def verify(self, message: bytes) -> bool:
        """Verify that the multisig is valid for the message."""
        try:
            self.validate()
        except (error.UnknownMsigVersionError, error.InvalidThresholdError):
            return False

        if sum(sig.signature is not None for sig in self.subsigs) < self.threshold:
            return False

        verified = 0
        for subsig in self.subsigs:
            if subsig.signature is None:
                continue
            verify_key = VerifyKey(subsig.public_key)
            try:
                verify_key.verify(message, subsig.signature)
                verified += 1
            except (BadSignatureError, ValueError, TypeError):
                return False

        return verified >= self.threshold

    def dictify(self) -> OrderedDict[str, object]:
        od = OrderedDict()
        od["subsig"] = [subsig.dictify() for subsig in self.subsigs]
        od["thr"] = self.threshold
        od["v"] = self.version
        return od

    def json_dictify(self) -> dict[str, object]:
        return {
            "subsig": [subsig.json_dictify() for subsig in self.subsigs],
            "thr": self.threshold,
            "v": self.version,
        }

    @staticmethod
    def undictify(data: dict[str, object]) -> "Multisig":
        subsigs = [MultisigSubsig.undictify(s) for s in data["subsig"]]  # type: ignore[index]
        msig = Multisig(data["v"], data["thr"], [])  # type: ignore[arg-type,index]
        msig.subsigs = subsigs
        return msig

    def get_multisig_account(self) -> "Multisig":
        """Return a Multisig object without signatures."""
        msig = Multisig(self.version, self.threshold, self.get_public_keys())
        for subsig in msig.subsigs:
            subsig.signature = None
        return msig

    def get_public_keys(self) -> list[str]:
        """Return the base32 encoded addresses for the multisig account."""
        keys = []
        for subsig in self.subsigs:
            encoded = encoding.encode_address(subsig.public_key)
            assert isinstance(encoded, str)
            keys.append(encoded)
        return keys

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Multisig):
            return False
        return (
            self.version == other.version
            and self.threshold == other.threshold
            and self.subsigs == other.subsigs
        )


class MultisigSubsig:
    """
    A public key + optional signature pair used by multisig accounts.
    """

    def __init__(self, public_key: bytes | str | None, signature: bytes | None = None) -> None:
        if isinstance(public_key, str):
            decoded = encoding.decode_address(public_key)
            if not isinstance(decoded, bytes):
                raise error.WrongChecksumError
            public_key = decoded
        self.public_key = public_key
        self.signature = signature

    def dictify(self) -> OrderedDict[str, object]:
        od = OrderedDict()
        od["pk"] = self.public_key
        if self.signature:
            od["s"] = self.signature
        return od

    def json_dictify(self) -> dict[str, str]:
        data = {"pk": base64.b64encode(self.public_key).decode()}  # type: ignore[arg-type]
        if self.signature:
            data["s"] = base64.b64encode(self.signature).decode()
        return data

    @staticmethod
    def undictify(data: dict[str, object]) -> "MultisigSubsig":
        signature = data.get("s")
        return MultisigSubsig(data["pk"], signature)  # type: ignore[arg-type]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MultisigSubsig):
            return False
        return self.public_key == other.public_key and self.signature == other.signature
