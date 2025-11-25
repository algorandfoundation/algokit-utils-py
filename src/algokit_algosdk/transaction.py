import base64
import binascii
import typing
from collections import OrderedDict

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from . import constants, encoding, error, logic


class Transaction(typing.Protocol):
    """
    Superclass for various transaction types.
    """

    sender: bytes | str

    def get_txid(self) -> str: ...

    def raw_sign(self, private_key: str) -> bytes: ...


class MultisigTransaction:
    """
    Represents a signed transaction.

    Args:
        transaction (Transaction): transaction that was signed
        multisig (Multisig): multisig account and signatures

    Attributes:
        transaction (Transaction)
        multisig (Multisig)
        auth_addr (str, optional)
    """

    def __init__(self, transaction: Transaction, multisig: "Multisig") -> None:
        self.transaction = transaction
        self.multisig = multisig

        msigAddr = multisig.address()
        if transaction.sender != msigAddr:
            self.auth_addr = msigAddr
        else:
            self.auth_addr = None

    def sign(self, private_key: str) -> None:
        """
        Sign the multisig transaction.

        Args:
            private_key (str): private key of signing account

        Note:
            A new signature will replace the old if there is already a
            signature for the address. To sign another transaction, you can
            either overwrite the signatures in the current Multisig, or you
            can use Multisig.get_multisig_account() to get a new multisig
            object with the same addresses.
        """
        self.multisig.validate()
        index = -1
        public_key = base64.b64decode(bytes(private_key, "utf-8"))
        public_key = public_key[constants.key_len_bytes :]
        for s in range(len(self.multisig.subsigs)):
            if self.multisig.subsigs[s].public_key == public_key:
                index = s
                break
        if index == -1:
            raise error.InvalidSecretKeyError
        sig = self.transaction.raw_sign(private_key)
        self.multisig.subsigs[index].signature = sig

    def get_txid(self) -> str:
        """
        Get the transaction's ID.

        Returns:
            str: transaction ID
        """
        return self.transaction.get_txid()

    def __eq__(self, other) -> bool:
        if isinstance(other, MultisigTransaction):
            return (
                self.transaction == other.transaction
                and self.auth_addr == other.auth_addr
                and self.multisig == other.multisig
            )

        return False


class Multisig:
    """
    Represents a multisig account and signatures.

    Args:
        version (int): currently, the version is 1
        threshold (int): how many signatures are necessary
        addresses (str[]): addresses in the multisig account

    Attributes:
        version (int)
        threshold (int)
        subsigs (MultisigSubsig[])
    """

    def __init__(self, version, threshold, addresses):
        self.version = version
        self.threshold = threshold
        self.subsigs = []
        for a in addresses:
            self.subsigs.append(MultisigSubsig(encoding.decode_address(a)))

    def validate(self):
        """Check if the multisig account is valid."""
        if not self.version == 1:
            raise error.UnknownMsigVersionError
        if self.threshold <= 0 or len(self.subsigs) == 0 or self.threshold > len(self.subsigs):
            raise error.InvalidThresholdError
        if len(self.subsigs) > constants.multisig_account_limit:
            raise error.MultisigAccountSizeError

    def address_bytes(self):
        """Return the raw bytes of the multisig account address."""
        msig_bytes = bytes(constants.msig_addr_prefix, "utf-8") + bytes([self.version]) + bytes([self.threshold])
        for s in self.subsigs:
            msig_bytes += s.public_key
        return encoding.checksum(msig_bytes)

    def address(self):
        """Return the multisig account address."""
        return encoding.encode_address(self.address_bytes())

    def verify(self, message):
        """Verify that the multisig is valid for the message."""
        try:
            self.validate()
        except (error.UnknownMsigVersionError, error.InvalidThresholdError):
            return False
        counter = sum(map(lambda s: s.signature is not None, self.subsigs))
        if counter < self.threshold:
            return False

        verified_count = 0
        for subsig in self.subsigs:
            if subsig.signature is not None:
                verify_key = VerifyKey(subsig.public_key)
                try:
                    verify_key.verify(message, subsig.signature)
                    verified_count += 1
                except (BadSignatureError, ValueError, TypeError):
                    return False

        if verified_count < self.threshold:
            return False

        return True

    def dictify(self):
        od = OrderedDict()
        od["subsig"] = [subsig.dictify() for subsig in self.subsigs]
        od["thr"] = self.threshold
        od["v"] = self.version
        return od

    def json_dictify(self):
        d = {
            "subsig": [subsig.json_dictify() for subsig in self.subsigs],
            "thr": self.threshold,
            "v": self.version,
        }
        return d

    @staticmethod
    def undictify(d):
        subsigs = [MultisigSubsig.undictify(s) for s in d["subsig"]]
        msig = Multisig(d["v"], d["thr"], [])
        msig.subsigs = subsigs
        return msig

    def get_multisig_account(self):
        """Return a Multisig object without signatures."""
        msig = Multisig(self.version, self.threshold, self.get_public_keys())
        for s in msig.subsigs:
            s.signature = None
        return msig

    def get_public_keys(self):
        """Return the base32 encoded addresses for the multisig account."""
        pks = [encoding.encode_address(s.public_key) for s in self.subsigs]
        return pks

    def __eq__(self, other):
        if not isinstance(other, Multisig):
            return False
        return self.version == other.version and self.threshold == other.threshold and self.subsigs == other.subsigs


class MultisigSubsig:
    """
    Attributes:
        public_key (bytes)
        signature (bytes)
    """

    def __init__(self, public_key, signature=None):
        self.public_key = public_key
        self.signature = signature

    def dictify(self):
        od = OrderedDict()
        od["pk"] = self.public_key
        if self.signature:
            od["s"] = self.signature
        return od

    def json_dictify(self):
        d = {"pk": base64.b64encode(self.public_key).decode()}
        if self.signature:
            d["s"] = base64.b64encode(self.signature).decode()
        return d

    @staticmethod
    def undictify(d):
        sig = None
        if "s" in d:
            sig = d["s"]
        mss = MultisigSubsig(d["pk"], sig)
        return mss

    def __eq__(self, other):
        if not isinstance(other, MultisigSubsig):
            return False
        return self.public_key == other.public_key and self.signature == other.signature


class LogicSig:
    """
    Represents a logic signature

    NOTE: LogicSig cannot sign transactions in all cases.  Instead, use LogicSigAccount as a safe, general purpose signing mechanism.  Since LogicSig does not track the provided signature's public key, LogicSig cannot sign transactions when delegated to a non-multisig account _and_ the sender is not the delegating account.

    Arguments:
        logic (bytes): compiled program
        args (list[bytes]): args are not signed, but are checked by logic

    Attributes:
        logic (bytes)
        sig (bytes)
        msig (Multisig)
        args (list[bytes])
    """

    def __init__(self, program, args=None):
        self._sanity_check_program(program)
        self.logic = program
        self.args = args
        self.sig = None
        self.msig = None
        self.lmsig = None

    @staticmethod
    def _sanity_check_program(program):
        """
        Performs heuristic program validation:
        check if passed in bytes are Algorand address, or they are B64 encoded, rather than Teal bytes

        Args:
            program (bytes): compiled program
        """

        def is_ascii_printable(program_bytes):
            return all(
                map(
                    lambda x: x == ord("\n") or (ord(" ") <= x <= ord("~")),
                    program_bytes,
                )
            )

        if not program:
            raise error.InvalidProgram("empty program")

        if is_ascii_printable(program):
            try:
                encoding.decode_address(program.decode("utf-8"))
                raise error.InvalidProgram("requesting program bytes, get Algorand address")
            except error.WrongChecksumError:
                pass
            except error.WrongKeyLengthError:
                pass

            try:
                base64.b64decode(program.decode("utf-8"))
                raise error.InvalidProgram("program should not be b64 encoded")
            except binascii.Error:
                pass

            raise error.InvalidProgram(
                "program bytes are all ASCII printable characters, not looking like Teal byte code"
            )

    def dictify(self):
        od = OrderedDict()
        if self.args:
            od["arg"] = self.args
        od["l"] = self.logic
        if self.sig:
            od["sig"] = base64.b64decode(self.sig)
        elif self.msig:
            od["msig"] = self.msig.dictify()
        elif self.lmsig:
            od["lmsig"] = self.lmsig.dictify()
        return od

    @staticmethod
    def undictify(d):
        lsig = LogicSig(d["l"], d.get("arg", None))
        if "sig" in d:
            lsig.sig = base64.b64encode(d["sig"]).decode()
        elif "msig" in d:
            lsig.msig = Multisig.undictify(d["msig"])
        elif "lmsig" in d:
            lsig.lmsig = Multisig.undictify(d["lmsig"])
        return lsig

    def sig_count(self):
        return int(self.sig is not None) + int(self.msig is not None) + int(self.lmsig is not None)

    def verify(self, public_key):
        """
        Verifies LogicSig against the transaction's sender address

        Args:
            public_key (bytes): sender address

        Returns:
            bool: true if the signature is valid (the sender address matches\
                the logic hash or the signature is valid against the sender\
                address), false otherwise
        """
        try:
            self._sanity_check_program(self.logic)
        except error.InvalidProgram:
            return False

        if self.sig_count() > 1:
            return False

        if self.sig:
            verify_key = VerifyKey(public_key)
            try:
                to_sign = constants.logic_prefix + self.logic
                verify_key.verify(to_sign, base64.b64decode(self.sig))
                return True
            except (BadSignatureError, ValueError, TypeError):
                return False

        if self.msig:
            to_sign = constants.logic_prefix + self.logic
            return self.msig.verify(to_sign)

        if self.lmsig:
            to_sign = constants.multisig_logic_prefix + self.lmsig.address_bytes() + self.logic
            return self.lmsig.verify(to_sign)

        # Non-delegated
        to_sign = constants.logic_prefix + self.logic
        return public_key == encoding.checksum(to_sign)

    def address(self):
        """
        Compute hash of the logic sig program (that is the same as escrow
        account address) as string address

        Returns:
            str: program address
        """
        return logic.address(self.logic)

    @staticmethod
    def sign_program(program, private_key):
        private_key = base64.b64decode(private_key)
        signing_key = SigningKey(private_key[: constants.key_len_bytes])
        to_sign = constants.logic_prefix + program
        signed = signing_key.sign(to_sign)
        return base64.b64encode(signed.signature).decode()

    @staticmethod
    def multisig_sign_program(program, private_key, multisig):
        private_key = base64.b64decode(private_key)
        signing_key = SigningKey(private_key[: constants.key_len_bytes])
        to_sign = constants.multisig_logic_prefix + multisig.address_bytes() + program
        signed = signing_key.sign(to_sign)
        return base64.b64encode(signed.signature).decode()

    @staticmethod
    def single_sig_multisig(program, private_key, multisig):
        index = -1
        public_key = base64.b64decode(bytes(private_key, "utf-8"))
        public_key = public_key[constants.key_len_bytes :]
        for s in range(len(multisig.subsigs)):
            if multisig.subsigs[s].public_key == public_key:
                index = s
                break
        if index == -1:
            raise error.InvalidSecretKeyError
        sig = LogicSig.multisig_sign_program(program, private_key, multisig)

        return sig, index

    def sign(self, private_key, multisig=None):
        """
        Creates signature (if no pk provided) or multi signature

        Args:
            private_key (str): private key of signing account
            multisig (Multisig): optional multisig account without signatures
                to sign with

        Raises:
            InvalidSecretKeyError: if no matching private key in multisig\
                object
            LogicSigOverspecifiedSignature: if the opposite signature type has
                already been provided
        """
        if not multisig:
            if self.msig or self.lmsig:
                raise error.LogicSigOverspecifiedSignature
            self.sig = LogicSig.sign_program(self.logic, private_key)
        else:
            if self.sig:
                raise error.LogicSigOverspecifiedSignature
            sig, index = LogicSig.single_sig_multisig(self.logic, private_key, multisig)
            multisig.subsigs[index].signature = base64.b64decode(sig)
            self.lmsig = multisig

    def append_to_multisig(self, private_key):
        """
        Appends a signature to multi signature

        Args:
            private_key (str): private key of signing account

        Raises:
            InvalidSecretKeyError: if no matching private key in multisig\
                object
        """
        if self.lmsig is None:
            raise error.InvalidSecretKeyError
        sig, index = LogicSig.single_sig_multisig(self.logic, private_key, self.lmsig)
        self.lmsig.subsigs[index].signature = base64.b64decode(sig)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LogicSig):
            return False
        return (
            self.logic == other.logic
            and self.args == other.args
            and self.sig == other.sig
            and self.msig == other.msig
            and self.lmsig == other.lmsig
        )


class LogicSigAccount:
    """
    Represents an account that can sign with a LogicSig program.

    Create a new LogicSigAccount. By default this constructs an escrow LogicSig account.
    Call `sign` or `sign_multisig` on the newly created LogicSigAccount to make it a delegated account.
    """

    def __init__(self, program: bytes, args: list[bytes] | None = None) -> None:
        self.lsig = LogicSig(program, args)
        self.sigkey: bytes | None = None

    def is_delegated(self) -> bool:
        """
        Check if this LogicSigAccount has been delegated to another account with
        a signature.

        Returns:
            bool: True if and only if this is a delegated LogicSigAccount.
        """
        return bool(self.lsig.sig or self.lsig.msig or self.lsig.lmsig)

    def verify(self) -> bool:
        """
        Verifies the LogicSig's program and signatures.

        Returns:
            bool: True if and only if the LogicSig program and signatures are
                valid.
        """
        addr = self.address()
        return self.lsig.verify(encoding.decode_address(addr))

    def sig_count(self) -> int:
        """
        Returns the number of cryptographic signatures on the LogicSig

        Returns:
            int: The number of signatures. Should never exceed 1.
        """
        return self.lsig.sig_count()

    def address(self) -> str:
        """
        Get the address of this LogicSigAccount.

        If the LogicSig is delegated to another account, this will return the
        address of that account.

        If the LogicSig is not delegated to another account, this will return an
        escrow address that is the hash of the LogicSig's program code.
        """
        if self.sig_count() > 1:
            raise error.LogicSigOverspecifiedSignature

        if self.lsig.sig:
            if not self.sigkey:
                raise error.LogicSigSigningKeyMissing
            return encoding.encode_address(self.sigkey)

        if self.lsig.msig:
            return self.lsig.msig.address()

        if self.lsig.lmsig:
            return self.lsig.lmsig.address()

        return self.lsig.address()

    def sign_multisig(self, multisig: Multisig, private_key: str) -> None:
        """
        Turns this LogicSigAccount into a delegated LogicSig.

        This type of LogicSig has the authority to sign transactions on behalf
        of another account, called the delegating account. Use this function if
        the delegating account is a multisig account.

        Args:
            multisig (Multisig): The multisig delegating account
            private_key (str): The private key of one of the members of the
                delegating multisig account. Use `append_to_multisig` to add
                additional signatures from other members.

        Raises:
            InvalidSecretKeyError: if no matching private key in multisig
                object
            LogicSigOverspecifiedSignature: if this LogicSigAccount has already
                been signed with a single private key.
        """
        self.lsig.sign(private_key, multisig)

    def append_to_multisig(self, private_key: str) -> None:
        """
        Adds an additional signature from a member of the delegating multisig
        account.

        Args:
            private_key (str): The private key of one of the members of the
                delegating multisig account.

        Raises:
            InvalidSecretKeyError: if no matching private key in multisig
                object
        """
        self.lsig.append_to_multisig(private_key)

    def sign(self, private_key: str) -> None:
        """
        Turns this LogicSigAccount into a delegated LogicSig.

        This type of LogicSig has the authority to sign transactions on behalf
        of another account, called the delegating account. If the delegating
        account is a multisig account, use `sign_multisig` instead.

        Args:
            private_key (str): The private key of the delegating account.

        Raises:
            LogicSigOverspecifiedSignature: if this LogicSigAccount has already
                been signed by a multisig account.
        """
        self.lsig.sign(private_key)
        public_key = base64.b64decode(bytes(private_key, "utf-8"))
        public_key = public_key[constants.key_len_bytes :]
        self.sigkey = public_key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LogicSigAccount):
            return False
        return self.lsig == other.lsig and self.sigkey == other.sigkey
