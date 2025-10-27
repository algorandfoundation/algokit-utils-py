from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence

__all__ = [
    "ClassicalSignatures",
    "CreateWalletRequest",
    "DeleteKeyRequest",
    "DeleteMultisigRequest",
    "DeletekeyResponse",
    "DeletemultisigResponse",
    "DigestRepresentsA32ByteValueHoldingThe256BitHashDigest",
    "Ed25519PrivateKey",
    "Ed25519PublicKey",
    "ExportKeyRequest",
    "ExportMasterKeyRequest",
    "ExportMultisigRequest",
    "GenerateKeyRequest",
    "GetwalletsResponse",
    "ImportKeyRequest",
    "ImportMultisigRequest",
    "InitWalletHandleTokenRequest",
    "ListKeysRequest",
    "ListMultisigRequest",
    "ListWalletsRequest",
    "MasterDerivationKey",
    "MultisigSig",
    "MultisigSubsig",
    "PostkeyExportResponse",
    "PostkeyImportResponse",
    "PostkeyListResponse",
    "PostkeyResponse",
    "PostmasterKeyExportResponse",
    "PostmultisigExportResponse",
    "PostmultisigImportResponse",
    "PostmultisigListResponse",
    "PostmultisigProgramSignResponse",
    "PostmultisigTransactionSignResponse",
    "PostprogramSignResponse",
    "PosttransactionSignResponse",
    "PostwalletInfoResponse",
    "PostwalletInitResponse",
    "PostwalletReleaseResponse",
    "PostwalletRenameResponse",
    "PostwalletRenewResponse",
    "PostwalletResponse",
    "PrivateKey",
    "PublicKey",
    "ReleaseWalletHandleTokenRequest",
    "RenameWalletRequest",
    "RenewWalletHandleTokenRequest",
    "SignMultisigRequest",
    "SignProgramMultisigRequest",
    "SignProgramRequest",
    "SignTransactionRequest",
    "Signature",
    "TxType",
    "VersionsRequest",
    "VersionsResponse",
    "Wallet",
    "WalletHandle",
    "WalletInfoRequest",
]


@dataclass(slots=True)
class CreateWalletRequest:
    """
    APIV1POSTWalletRequest is the request for `POST /v1/wallet`
    """

    master_derivation_key: list[int] = field(
        default=None,
        metadata=wire("master_derivation_key"),
    )
    wallet_driver_name: str = field(
        default=None,
        metadata=wire("wallet_driver_name"),
    )
    wallet_name: str = field(
        default=None,
        metadata=wire("wallet_name"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class DeletekeyResponse:
    """
    APIV1DELETEKeyResponse is the response to `DELETE /v1/key`
    friendly:DeleteKeyResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )


@dataclass(slots=True)
class DeletemultisigResponse:
    """
    APIV1DELETEMultisigResponse is the response to POST /v1/multisig/delete`
    friendly:DeleteMultisigResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )


@dataclass(slots=True)
class DeleteKeyRequest:
    """
    APIV1DELETEKeyRequest is the request for `DELETE /v1/key`
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class DeleteMultisigRequest:
    """
    APIV1DELETEMultisigRequest is the request for `DELETE /v1/multisig`
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class ExportKeyRequest:
    """
    APIV1POSTKeyExportRequest is the request for `POST /v1/key/export`
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class ExportMasterKeyRequest:
    """
    APIV1POSTMasterKeyExportRequest is the request for `POST /v1/master-key/export`
    """

    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class ExportMultisigRequest:
    """
    APIV1POSTMultisigExportRequest is the request for `POST /v1/multisig/export`
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


@dataclass(slots=True)
class GetwalletsResponse:
    """
    APIV1GETWalletsResponse is the response to `GET /v1/wallets`
    friendly:ListWalletsResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    wallets: list[Wallet] = field(
        default=None,
        metadata=wire(
            "wallets", encode=encode_model_sequence, decode=lambda raw: decode_model_sequence(lambda: Wallet, raw)
        ),
    )


@dataclass(slots=True)
class GenerateKeyRequest:
    """
    APIV1POSTKeyRequest is the request for `POST /v1/key`
    """

    display_mnemonic: bool = field(
        default=None,
        metadata=wire("display_mnemonic"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


@dataclass(slots=True)
class ImportKeyRequest:
    """
    APIV1POSTKeyImportRequest is the request for `POST /v1/key/import`
    """

    private_key: bytes = field(
        default=None,
        metadata=wire("private_key"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


@dataclass(slots=True)
class ImportMultisigRequest:
    """
    APIV1POSTMultisigImportRequest is the request for `POST /v1/multisig/import`
    """

    multisig_version: int = field(
        default=None,
        metadata=wire("multisig_version"),
    )
    pks: list[list[int]] = field(
        default=None,
        metadata=wire("pks"),
    )
    threshold: int = field(
        default=None,
        metadata=wire("threshold"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


@dataclass(slots=True)
class InitWalletHandleTokenRequest:
    """
    APIV1POSTWalletInitRequest is the request for `POST /v1/wallet/init`
    """

    wallet_id: str = field(
        default=None,
        metadata=wire("wallet_id"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class ListKeysRequest:
    """
    APIV1POSTKeyListRequest is the request for `POST /v1/key/list`
    """

    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


@dataclass(slots=True)
class ListMultisigRequest:
    """
    APIV1POSTMultisigListRequest is the request for `POST /v1/multisig/list`
    """

    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


@dataclass(slots=True)
class ListWalletsRequest:
    """
    APIV1GETWalletsRequest is the request for `GET /v1/wallets`
    """


@dataclass(slots=True)
class MultisigSig:
    """
    MultisigSig is the structure that holds multiple Subsigs
    """

    subsigs: list[MultisigSubsig] = field(
        default=None,
        metadata=wire(
            "Subsigs",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: MultisigSubsig, raw),
        ),
    )
    threshold: int = field(
        default=None,
        metadata=wire("Threshold"),
    )
    version: int = field(
        default=None,
        metadata=wire("Version"),
    )


@dataclass(slots=True)
class MultisigSubsig:
    """
    MultisigSubsig is a struct that holds a pair of public key and signatures
    signatures may be empty
    """

    key: list[int] = field(
        default=None,
        metadata=wire("Key"),
    )
    sig: list[int] = field(
        default=None,
        metadata=wire("Sig"),
    )


@dataclass(slots=True)
class PostkeyExportResponse:
    """
    APIV1POSTKeyExportResponse is the response to `POST /v1/key/export`
    friendly:ExportKeyResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    private_key: bytes = field(
        default=None,
        metadata=wire("private_key"),
    )


@dataclass(slots=True)
class PostkeyImportResponse:
    """
    APIV1POSTKeyImportResponse is the response to `POST /v1/key/import`
    friendly:ImportKeyResponse
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )


@dataclass(slots=True)
class PostkeyListResponse:
    """
    APIV1POSTKeyListResponse is the response to `POST /v1/key/list`
    friendly:ListKeysResponse
    """

    addresses: list[str] = field(
        default=None,
        metadata=wire("addresses"),
    )
    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )


@dataclass(slots=True)
class PostkeyResponse:
    """
    APIV1POSTKeyResponse is the response to `POST /v1/key`
    friendly:GenerateKeyResponse
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )


@dataclass(slots=True)
class PostmasterKeyExportResponse:
    """
    APIV1POSTMasterKeyExportResponse is the response to `POST /v1/master-key/export`
    friendly:ExportMasterKeyResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    master_derivation_key: list[int] = field(
        default=None,
        metadata=wire("master_derivation_key"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )


@dataclass(slots=True)
class PostmultisigExportResponse:
    """
    APIV1POSTMultisigExportResponse is the response to `POST /v1/multisig/export`
    friendly:ExportMultisigResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    multisig_version: int = field(
        default=None,
        metadata=wire("multisig_version"),
    )
    pks: list[list[int]] = field(
        default=None,
        metadata=wire("pks"),
    )
    threshold: int = field(
        default=None,
        metadata=wire("threshold"),
    )


@dataclass(slots=True)
class PostmultisigImportResponse:
    """
    APIV1POSTMultisigImportResponse is the response to `POST /v1/multisig/import`
    friendly:ImportMultisigResponse
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )


@dataclass(slots=True)
class PostmultisigListResponse:
    """
    APIV1POSTMultisigListResponse is the response to `POST /v1/multisig/list`
    friendly:ListMultisigResponse
    """

    addresses: list[str] = field(
        default=None,
        metadata=wire("addresses"),
    )
    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )


@dataclass(slots=True)
class PostmultisigProgramSignResponse:
    """
    APIV1POSTMultisigProgramSignResponse is the response to `POST /v1/multisig/signdata`
    friendly:SignProgramMultisigResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    multisig: bytes = field(
        default=None,
        metadata=wire("multisig"),
    )


@dataclass(slots=True)
class PostmultisigTransactionSignResponse:
    """
    APIV1POSTMultisigTransactionSignResponse is the response to `POST /v1/multisig/sign`
    friendly:SignMultisigResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    multisig: bytes = field(
        default=None,
        metadata=wire("multisig"),
    )


@dataclass(slots=True)
class PostprogramSignResponse:
    """
    APIV1POSTProgramSignResponse is the response to `POST /v1/data/sign`
    friendly:SignProgramResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    sig: bytes = field(
        default=None,
        metadata=wire("sig"),
    )


@dataclass(slots=True)
class PosttransactionSignResponse:
    """
    APIV1POSTTransactionSignResponse is the response to `POST /v1/transaction/sign`
    friendly:SignTransactionResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    signed_transaction: bytes = field(
        default=None,
        metadata=wire("signed_transaction"),
    )


@dataclass(slots=True)
class PostwalletInfoResponse:
    """
    APIV1POSTWalletInfoResponse is the response to `POST /v1/wallet/info`
    friendly:WalletInfoResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    wallet_handle: WalletHandle = field(
        default=None,
        metadata=nested("wallet_handle", lambda: WalletHandle),
    )


@dataclass(slots=True)
class PostwalletInitResponse:
    """
    APIV1POSTWalletInitResponse is the response to `POST /v1/wallet/init`
    friendly:InitWalletHandleTokenResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


@dataclass(slots=True)
class PostwalletReleaseResponse:
    """
    APIV1POSTWalletReleaseResponse is the response to `POST /v1/wallet/release`
    friendly:ReleaseWalletHandleTokenResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )


@dataclass(slots=True)
class PostwalletRenameResponse:
    """
    APIV1POSTWalletRenameResponse is the response to `POST /v1/wallet/rename`
    friendly:RenameWalletResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    wallet: Wallet = field(
        default=None,
        metadata=nested("wallet", lambda: Wallet),
    )


@dataclass(slots=True)
class PostwalletRenewResponse:
    """
    APIV1POSTWalletRenewResponse is the response to `POST /v1/wallet/renew`
    friendly:RenewWalletHandleTokenResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    wallet_handle: WalletHandle = field(
        default=None,
        metadata=nested("wallet_handle", lambda: WalletHandle),
    )


@dataclass(slots=True)
class PostwalletResponse:
    """
    APIV1POSTWalletResponse is the response to `POST /v1/wallet`
    friendly:CreateWalletResponse
    """

    error: bool = field(
        default=None,
        metadata=wire("error"),
    )
    message: str = field(
        default=None,
        metadata=wire("message"),
    )
    wallet: Wallet = field(
        default=None,
        metadata=nested("wallet", lambda: Wallet),
    )


@dataclass(slots=True)
class ReleaseWalletHandleTokenRequest:
    """
    APIV1POSTWalletReleaseRequest is the request for `POST /v1/wallet/release`
    """

    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


@dataclass(slots=True)
class RenameWalletRequest:
    """
    APIV1POSTWalletRenameRequest is the request for `POST /v1/wallet/rename`
    """

    wallet_id: str = field(
        default=None,
        metadata=wire("wallet_id"),
    )
    wallet_name: str = field(
        default=None,
        metadata=wire("wallet_name"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class RenewWalletHandleTokenRequest:
    """
    APIV1POSTWalletRenewRequest is the request for `POST /v1/wallet/renew`
    """

    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


@dataclass(slots=True)
class SignMultisigRequest:
    """
    APIV1POSTMultisigTransactionSignRequest is the request for `POST /v1/multisig/sign`
    """

    partial_multisig: MultisigSig = field(
        default=None,
        metadata=nested("partial_multisig", lambda: MultisigSig),
    )
    public_key: list[int] = field(
        default=None,
        metadata=wire("public_key"),
    )
    signer: list[int] = field(
        default=None,
        metadata=wire("signer"),
    )
    transaction: bytes = field(
        default=None,
        metadata=wire("transaction"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class SignProgramMultisigRequest:
    """
    APIV1POSTMultisigProgramSignRequest is the request for `POST /v1/multisig/signprogram`
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    data: bytes = field(
        default=None,
        metadata=wire("data"),
    )
    partial_multisig: MultisigSig = field(
        default=None,
        metadata=nested("partial_multisig", lambda: MultisigSig),
    )
    public_key: list[int] = field(
        default=None,
        metadata=wire("public_key"),
    )
    use_legacy_msig: bool = field(
        default=None,
        metadata=wire("use_legacy_msig"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class SignProgramRequest:
    """
    APIV1POSTProgramSignRequest is the request for `POST /v1/program/sign`
    """

    address: str = field(
        default=None,
        metadata=wire("address"),
    )
    data: bytes = field(
        default=None,
        metadata=wire("data"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class SignTransactionRequest:
    """
    APIV1POSTTransactionSignRequest is the request for `POST /v1/transaction/sign`
    """

    public_key: list[int] = field(
        default=None,
        metadata=wire("public_key"),
    )
    transaction: bytes = field(
        default=None,
        metadata=wire("transaction"),
    )
    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str = field(
        default=None,
        metadata=wire("wallet_password"),
    )


@dataclass(slots=True)
class VersionsRequest:
    """
    VersionsRequest is the request for `GET /versions`
    """


@dataclass(slots=True)
class VersionsResponse:
    """
    VersionsResponse is the response to `GET /versions`
    friendly:VersionsResponse
    """

    versions: list[str] = field(
        default=None,
        metadata=wire("versions"),
    )


@dataclass(slots=True)
class Wallet:
    """
    APIV1Wallet is the API's representation of a wallet
    """

    driver_name: str = field(
        default=None,
        metadata=wire("driver_name"),
    )
    driver_version: int = field(
        default=None,
        metadata=wire("driver_version"),
    )
    id_: str = field(
        default=None,
        metadata=wire("id"),
    )
    mnemonic_ux: bool = field(
        default=None,
        metadata=wire("mnemonic_ux"),
    )
    name: str = field(
        default=None,
        metadata=wire("name"),
    )
    supported_txs: list[str] = field(
        default=None,
        metadata=wire("supported_txs"),
    )


@dataclass(slots=True)
class WalletHandle:
    """
    APIV1WalletHandle includes the wallet the handle corresponds to
    and the number of number of seconds to expiration
    """

    expires_seconds: int = field(
        default=None,
        metadata=wire("expires_seconds"),
    )
    wallet: Wallet = field(
        default=None,
        metadata=nested("wallet", lambda: Wallet),
    )


@dataclass(slots=True)
class WalletInfoRequest:
    """
    APIV1POSTWalletInfoRequest is the request for `POST /v1/wallet/info`
    """

    wallet_handle_token: str = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )


DigestRepresentsA32ByteValueHoldingThe256BitHashDigest = list[int]
MasterDerivationKey = list[int]
PrivateKey = list[int]
PublicKey = list[int]
Signature = list[int]
TxType = str
Ed25519PrivateKey = list[int]
Ed25519PublicKey = list[int]
ClassicalSignatures = list[int]
