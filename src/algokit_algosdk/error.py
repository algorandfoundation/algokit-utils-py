# Vendored from py-algorand-sdk/algosdk/error.py (MIT License).


class BadTxnSenderError(Exception):
    def __init__(self) -> None:
        super().__init__("transaction sender does not match multisig parameters")


class InvalidThresholdError(Exception):
    def __init__(self) -> None:
        super().__init__("invalid multisig threshold")


class InvalidSecretKeyError(Exception):
    def __init__(self) -> None:
        super().__init__("secret key has no corresponding public key in multisig")


class MergeKeysMismatchError(Exception):
    def __init__(self) -> None:
        super().__init__("multisig parameters do not match")


class MergeAuthAddrMismatchError(Exception):
    def __init__(self) -> None:
        super().__init__("multisig transaction auth addresses do not match")


class DuplicateSigMismatchError(Exception):
    def __init__(self) -> None:
        super().__init__("mismatched duplicate signatures in multisig")


class LogicSigOverspecifiedSignature(Exception):
    def __init__(self) -> None:
        super().__init__("LogicSig has too many signatures. At most one of sig or msig may be present")


class LogicSigSigningKeyMissing(Exception):
    def __init__(self) -> None:
        super().__init__("LogicSigAccount is missing signing key")


class WrongAmountType(Exception):
    def __init__(self) -> None:
        super().__init__("amount (amt) must be a non-negative integer")


class WrongChecksumError(Exception):
    def __init__(self) -> None:
        super().__init__("checksum failed to validate")


class WrongKeyLengthError(Exception):
    def __init__(self) -> None:
        super().__init__("key length must be 58")


class WrongMnemonicLengthError(Exception):
    def __init__(self) -> None:
        super().__init__("mnemonic length must be 25")


class WrongHashLengthError(Exception):
    """General error that is normally changed to be more specific"""

    def __init__(self) -> None:
        super().__init__("length must be 32 bytes")


class WrongKeyBytesLengthError(Exception):
    def __init__(self) -> None:
        super().__init__("key length in bytes must be 32")


class UnknownMsigVersionError(Exception):
    def __init__(self) -> None:
        super().__init__("unknown multisig version != 1")


class WrongMetadataLengthError(Exception):
    def __init__(self) -> None:
        super().__init__("metadata length must be 32 bytes")


class WrongLeaseLengthError(Exception):
    def __init__(self) -> None:
        super().__init__("lease length must be 32 bytes")


class WrongNoteType(Exception):
    def __init__(self) -> None:
        super().__init__('note must be of type "bytes"')


class WrongNoteLength(Exception):
    def __init__(self) -> None:
        super().__init__("note length must be at most 1024")


class InvalidProgram(Exception):
    def __init__(self, message: str = "invalid program for logic sig") -> None:
        super().__init__(message)


class TransactionGroupSizeError(Exception):
    def __init__(self) -> None:
        super().__init__("transaction groups are limited to 16 transactions")


class MultisigAccountSizeError(Exception):
    def __init__(self) -> None:
        super().__init__("multisig accounts are limited to 256 addresses")


class OutOfRangeDecimalsError(Exception):
    def __init__(self) -> None:
        super().__init__("decimals must be between 0 and 19, inclusive")


class EmptyAddressError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "manager, freeze, reserve, and clawback should not be empty unless strict_empty_address_check is set to False",
        )


class OverspecifiedRoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Two arguments were given for the round or block number; please only give one")


class UnderspecifiedRoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Please specify a round number")


class ZeroAddressError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "For the zero address, please specify AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
        )


class KeyregOnlineTxnInitError(Exception):
    def __init__(self, attr: str) -> None:
        super().__init__(attr + " should not be None")


class KMDHTTPError(Exception):
    pass


class AlgodRequestError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class AlgodHTTPError(Exception):
    def __init__(self, msg: str, code: int | None = None, data: str | None = None) -> None:
        super().__init__(msg)
        self.code = code
        self.data = data


class AlgodResponseError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class IndexerHTTPError(Exception):
    pass


class ConfirmationTimeoutError(Exception):
    pass


class TransactionRejectedError(Exception):
    pass
