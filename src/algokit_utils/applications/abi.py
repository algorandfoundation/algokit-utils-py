from __future__ import annotations

import base64
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeAlias, cast

from typing_extensions import deprecated

from algokit_abi import abi, arc56
from algokit_algod_client import models as algod_models
from algokit_utils.models.state import BoxName

ABIValue: TypeAlias = (
    bool | int | str | bytes | bytearray | list["ABIValue"] | tuple["ABIValue"] | dict[str, "ABIValue"] | object
)
ABIStruct: TypeAlias = dict[str, list[dict[str, "ABIValue"]]] | object
Arc56ReturnValueType: TypeAlias = ABIValue | ABIStruct | None

ABIType: TypeAlias = abi.ABIType
ABIArgumentType: TypeAlias = abi.ABIType | arc56.TransactionType | arc56.ReferenceType
Arc56Method: TypeAlias = arc56.Method
ConfirmationResponse: TypeAlias = algod_models.PendingTransactionResponse

ABI_RETURN_HASH = b"\x15\x1f\x7c\x75"
ABI_RETURN_PREFIX_LENGTH = len(ABI_RETURN_HASH)


def _warn_deprecated(message: str) -> None:
    warnings.warn(message, DeprecationWarning, stacklevel=3)


@dataclass(slots=True)
class ABIReturn:
    """Represents the return value from an ABI method call.

    Aligns with the Rust model: always carries the method, raw bytes, decoded value (if available),
    and any decode error. Transaction context should live on the send result, not here.
    """

    method: Arc56Method | None
    raw_value: bytes
    value: ABIValue | None
    decode_error: Exception | None
    _tx_info: ConfirmationResponse | None = None

    def __init__(
        self,
        *,
        method: Arc56Method | None,
        raw_value: bytes = b"",
        value: ABIValue | None = None,
        decode_error: Exception | None = None,
        tx_info: ConfirmationResponse | None = None,
    ) -> None:
        self.method = method
        self.raw_value = raw_value or b""
        self.value = value
        self.decode_error = decode_error
        self._tx_info = tx_info

    @property
    def is_success(self) -> bool:
        """Returns True if the ABI call was decoded successfully."""
        return self.decode_error is None

    @property
    @deprecated(
        "ABIReturn.tx_info is deprecated; read the transaction confirmation from the send result "
        "(e.g. SendAppTransactionResult.confirmation)."
    )
    def tx_info(self) -> ConfirmationResponse | None:
        """Deprecated: transaction info now lives on the send result."""
        _warn_deprecated(
            "ABIReturn.tx_info is deprecated; read the transaction confirmation from the send result "
            "(e.g. SendAppTransactionResult.confirmation)."
        )
        return self._tx_info

    def get_arc56_value(self, method: arc56.Method, structs: dict[str, object] | None = None) -> Arc56ReturnValueType:
        """Deprecated: use `value` directly."""
        _warn_deprecated("ABIReturn.get_arc56_value is deprecated; use `ABIReturn.value` instead.")
        return get_arc56_value(self, method, structs)


@dataclass(slots=True)
@deprecated("ABIResult is deprecated; call extract_abi_return_from_logs(...) and work with ABIReturn instead.")
class ABIResult(ABIReturn):
    """Deprecated wrapper that previously carried tx context plus ABI data."""

    tx_id: str | None = None

    def __init__(
        self,
        *,
        tx_id: str | None = None,
        raw_value: bytes = b"",
        value: ABIValue | None = None,
        decode_error: Exception | None = None,
        tx_info: ConfirmationResponse | None = None,
        method: Arc56Method | None = None,
    ) -> None:
        _warn_deprecated("ABIResult is deprecated; call extract_abi_return_from_logs(...) and use ABIReturn instead.")
        super().__init__(method=method, raw_value=raw_value, value=value, decode_error=decode_error, tx_info=tx_info)
        self.tx_id = tx_id

    @classmethod
    @deprecated(
        "ABIResult.from_abireturn is deprecated; keep the tx_id alongside the send result and use ABIReturn directly."
    )
    def from_abireturn(cls, abi_return: ABIReturn, tx_id: str | None = None) -> ABIResult:
        _warn_deprecated(
            "ABIResult.from_abireturn is deprecated; keep the tx_id alongside the send result "
            "and use ABIReturn directly."
        )
        return cls(
            tx_id=tx_id,
            raw_value=abi_return.raw_value,
            value=abi_return.value,
            decode_error=abi_return.decode_error,
            tx_info=abi_return._tx_info,  # noqa: SLF001
            method=abi_return.method,
        )


def _decode_log_entry(log_entry: bytes | bytearray | memoryview | str) -> bytes:
    return bytes(log_entry) if isinstance(log_entry, bytes | bytearray | memoryview) else base64.b64decode(log_entry)


def extract_abi_return_from_logs(confirmation: ConfirmationResponse, method: Arc56Method) -> ABIReturn:
    """Decode ABI return value from a transaction confirmation log."""
    returns = method.returns
    return_type = returns.type if returns else arc56.Void

    if return_type == arc56.Void:
        return ABIReturn(method=method, raw_value=b"", value=None, decode_error=None, tx_info=confirmation)

    logs: Sequence[bytes | bytearray | memoryview | str | None] = confirmation.logs or []
    if not logs:
        return ABIReturn(
            method=method,
            raw_value=b"",
            value=None,
            decode_error=ValueError("App call transaction did not log a return value"),
            tx_info=confirmation,
        )

    last_log = logs[-1]
    if last_log is None:
        return ABIReturn(
            method=method,
            raw_value=b"",
            value=None,
            decode_error=ValueError("App call transaction did not log a return value"),
            tx_info=confirmation,
        )

    result_bytes = _decode_log_entry(last_log)
    if len(result_bytes) < ABI_RETURN_PREFIX_LENGTH or result_bytes[:ABI_RETURN_PREFIX_LENGTH] != ABI_RETURN_HASH:
        return ABIReturn(
            method=method,
            raw_value=b"",
            value=None,
            decode_error=ValueError("App call transaction did not log a return value"),
            tx_info=confirmation,
        )

    raw_value = result_bytes[ABI_RETURN_PREFIX_LENGTH:]
    method_return_type = cast(abi.ABIType, return_type)
    try:
        decoded = method_return_type.decode(raw_value)
        return ABIReturn(
            method=method,
            raw_value=raw_value,
            value=decoded,
            decode_error=None,
            tx_info=confirmation,
        )
    except Exception as err:
        return ABIReturn(
            method=method,
            raw_value=raw_value,
            value=None,
            decode_error=err,
            tx_info=confirmation,
        )


@deprecated("parse_abi_method_result is deprecated; call extract_abi_return_from_logs(confirmation, method) instead.")
def parse_abi_method_result(method: Arc56Method, tx_id: str, txn: ConfirmationResponse) -> ABIResult:
    """Deprecated: use extract_abi_return_from_logs instead."""
    _warn_deprecated("parse_abi_method_result is deprecated; call extract_abi_return_from_logs(confirmation, method).")
    abi_return = extract_abi_return_from_logs(txn, method)
    return ABIResult.from_abireturn(abi_return, tx_id)


@deprecated("get_arc56_value is deprecated; use ABIReturn.value instead.")
def get_arc56_value(
    abi_return: ABIReturn, method: arc56.Method, structs: dict[str, object] | None = None
) -> Arc56ReturnValueType:
    """Deprecated: use `ABIReturn.value` instead."""
    _warn_deprecated("get_arc56_value is deprecated; use ABIReturn.value instead.")
    _ = method  # Accepted for compatibility with generated clients
    _ = structs  # Accepted for compatibility with generated clients
    if abi_return.decode_error:
        raise ValueError(abi_return.decode_error)
    return abi_return.value


__all__ = [
    "ABIArgumentType",
    "ABIResult",
    "ABIReturn",
    "ABIStruct",
    "ABIType",
    "ABIValue",
    "Arc56ReturnValueType",
    "BoxABIValue",
    "extract_abi_return_from_logs",
    "get_abi_decoded_value",
    "get_abi_encoded_value",
    "get_arc56_value",
    "parse_abi_method_result",
]


def get_abi_encoded_value(value: object, abi_type: abi.ABIType | arc56.AVMType) -> bytes:
    """Encodes a value according to its ABI type.

    :param value: The value to encode
    :param abi_type: The ABI or AVM type
    :return: The ABI encoded bytes
    """
    if isinstance(value, (bytes | bytearray)):
        return bytes(value)
    if abi_type == arc56.AVMType.UINT64 and isinstance(value, int):
        return abi.ABIType.from_string("uint64").encode(value)
    if abi_type == arc56.AVMType.STRING and isinstance(value, str):
        return value.encode("utf-8")
    if abi_type == arc56.AVMType.BYTES and isinstance(value, bytes | bytearray):
        return bytes(value)
    assert not isinstance(abi_type, arc56.AVMType), "unexpected AVMType"
    return abi_type.encode(value)


def get_abi_decoded_value(
    value: bytes | int | str,
    decode_type: arc56.AVMType | abi.ABIType | arc56.ReferenceType,
) -> ABIValue:
    """Decodes a value according to its ABI type.

    :param value: The value to decode
    :param decode_type: The ABI type string or type object
    :return: The decoded ABI value
    """

    # map reference types to their value equivalents
    if decode_type in (arc56.ReferenceType.ASSET, arc56.ReferenceType.APPLICATION):
        decode_type = abi.UintType(64)
    elif decode_type == arc56.ReferenceType.ACCOUNT:
        decode_type = abi.AddressType()
    if decode_type == arc56.AVMType.UINT64:
        decode_type = abi.UintType(64)
    if decode_type == arc56.AVMType.BYTES or not isinstance(value, bytes):
        return value
    if decode_type == arc56.AVMType.STRING:
        return value.decode("utf-8")
    assert isinstance(decode_type, abi.ABIType), "unexpected ABIType"
    return decode_type.decode(value)  # type: ignore[no-any-return]


@dataclass(kw_only=True, frozen=True)
class BoxABIValue:
    """Represents an ABI value stored in a box."""

    name: BoxName
    """The name of the box"""
    value: ABIValue
    """The ABI value stored in the box"""
