import base64
import binascii
from collections import OrderedDict
from typing import Sequence

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from . import constants, encoding, error
from .multisig import Multisig

# Vendored from py-algorand-sdk/algosdk/transaction.py (logic sig sections) under MIT License.

__all__ = ["LogicSig", "LogicSigAccount"]


class LogicSig:
    """
    Represents a logic signature consisting of compiled TEAL bytes and optional arguments.
    """

    def __init__(self, program: bytes, args: Sequence[bytes] | None = None) -> None:
        self._sanity_check_program(program)
        self.logic = program
        self.args = list(args) if args else None
        self.sig: str | None = None
        self.msig: Multisig | None = None
        self.lmsig: Multisig | None = None

    @staticmethod
    def _sanity_check_program(program: bytes) -> None:
        """
        Reject common user mistakes (passing addresses or base64 strings instead of bytecode).
        """

        def is_ascii_printable(program_bytes: bytes) -> bool:
            return all(x == ord("\n") or (ord(" ") <= x <= ord("~")) for x in program_bytes)

        if not program:
            raise error.InvalidProgram("empty program")

        if is_ascii_printable(program):
            try:
                encoding.decode_address(program.decode("utf-8"))
                raise error.InvalidProgram("requesting program bytes, got Algorand address")
            except (error.WrongChecksumError, error.WrongKeyLengthError):
                pass

            try:
                base64.b64decode(program.decode("utf-8"))
                raise error.InvalidProgram("program should not be b64 encoded")
            except binascii.Error:
                pass

            raise error.InvalidProgram("program bytes look ASCII, not compiled TEAL")

    def dictify(self) -> OrderedDict[str, object]:
        payload: OrderedDict[str, object] = OrderedDict()
        if self.args:
            payload["arg"] = self.args
        payload["l"] = self.logic
        if self.sig:
            payload["sig"] = base64.b64decode(self.sig)
        elif self.msig:
            payload["msig"] = self.msig.dictify()
        elif self.lmsig:
            payload["lmsig"] = self.lmsig.dictify()
        return payload

    @staticmethod
    def undictify(data: dict[str, object]) -> "LogicSig":
        lsig = LogicSig(data["l"], data.get("arg"))  # type: ignore[arg-type]
        if "sig" in data:
            lsig.sig = base64.b64encode(data["sig"]).decode()  # type: ignore[arg-type]
        elif "msig" in data:
            lsig.msig = Multisig.undictify(data["msig"])  # type: ignore[arg-type]
        elif "lmsig" in data:
            lsig.lmsig = Multisig.undictify(data["lmsig"])  # type: ignore[arg-type]
        return lsig

    def sig_count(self) -> int:
        return int(self.sig is not None) + int(self.msig is not None) + int(self.lmsig is not None)

    def verify(self, public_key: bytes) -> bool:
        """Verifies LogicSig against the provided sender address bytes."""
        try:
            self._sanity_check_program(self.logic)
        except error.InvalidProgram:
            return False

        if self.sig_count() > 1:
            return False

        if self.sig:
            verify_key = VerifyKey(public_key)
            to_sign = constants.logic_prefix + self.logic
            try:
                verify_key.verify(to_sign, base64.b64decode(self.sig))
                return True
            except (BadSignatureError, ValueError, TypeError):
                return False

        if self.msig:
            to_sign = constants.logic_prefix + self.logic
            return self.msig.verify(to_sign)

        if self.lmsig:
            to_sign = constants.multisig_logic_prefix + self.logic
            return self.lmsig.verify(to_sign)

        addr = self.address()
        encoded = encoding.encode_address(public_key)
        return addr == encoded

    def sign(self, private_key: str, multisig: Multisig | None = None) -> None:
        """
        Sign the program bytes. If `multisig` is provided, append the signature to that multisig.
        """
        if self.sig_count() > 0 and not multisig:
            raise error.LogicSigOverspecifiedSignature

        private_key_bytes = base64.b64decode(private_key)
        signing_key = SigningKey(private_key_bytes[: constants.key_len_bytes])
        to_sign = constants.logic_prefix + self.logic

        if not multisig:
            signature = signing_key.sign(to_sign).signature
            self.sig = base64.b64encode(signature).decode()
            self.msig = None
            self.lmsig = None
            return

        # Multisig signing
        sig = signing_key.sign(constants.logic_prefix + self.logic).signature
        for idx, subsig in enumerate(multisig.subsigs):
            if subsig.public_key == signing_key.verify_key.encode():
                if not subsig.signature:
                    subsig.signature = sig
                    self.msig = multisig
                    self.sig = None
                    self.lmsig = None
                    return
                subsig.signature = sig
                self.msig = multisig
                self.sig = None
                self.lmsig = None
                return

        raise error.InvalidSecretKeyError

    def append_to_multisig(self, private_key: str) -> None:
        if not self.msig:
            raise error.InvalidSecretKeyError
        self.sign(private_key, self.msig)

    def address(self) -> str:
        """Return the hash of the program bytes as an address."""
        checksum = encoding.checksum(constants.logic_prefix + self.logic)
        encoded = encoding.encode_address(checksum)
        assert isinstance(encoded, str)
        return encoded


class LogicSigAccount:
    """
    Safe wrapper around LogicSig that tracks the signing key for delegated logic.
    """

    def __init__(self, program: bytes, args: Sequence[bytes] | None = None) -> None:
        self.lsig = LogicSig(program, args)
        self.sigkey: bytes | None = None

    def dictify(self) -> OrderedDict[str, object]:
        payload = OrderedDict()
        payload["lsig"] = self.lsig.dictify()
        if self.sigkey:
            payload["sigkey"] = self.sigkey
        return payload

    @staticmethod
    def undictify(data: dict[str, object]) -> "LogicSigAccount":
        account = LogicSigAccount(b"", [])
        account.lsig = LogicSig.undictify(data["lsig"])  # type: ignore[arg-type]
        account.sigkey = data.get("sigkey")  # type: ignore[assignment]
        return account

    def verify(self, public_key: bytes) -> bool:
        return self.lsig.verify(public_key)

    def address(self) -> str:
        if self.sigkey:
            encoded = encoding.encode_address(self.sigkey)
            assert isinstance(encoded, str)
            return encoded
        if self.lsig.msig:
            return self.lsig.msig.address()
        if self.lsig.lmsig:
            return self.lsig.lmsig.address()
        return self.lsig.address()

    def sign_multisig(self, multisig: Multisig, private_key: str) -> None:
        if self.lsig.sig:
            raise error.LogicSigOverspecifiedSignature
        self.lsig.sign(private_key, multisig)
        self.sigkey = None

    def append_to_multisig(self, private_key: str) -> None:
        if not self.lsig.msig:
            raise error.InvalidSecretKeyError
        self.lsig.append_to_multisig(private_key)
        self.sigkey = None

    def sign(self, private_key: str) -> None:
        if self.lsig.msig:
            raise error.LogicSigOverspecifiedSignature
        self.lsig.sign(private_key)
        decoded = base64.b64decode(bytes(private_key, "utf-8"))
        self.sigkey = decoded[constants.key_len_bytes :]
