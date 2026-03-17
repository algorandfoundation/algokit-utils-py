"""Generated Pydantic validation schemas from OpenAPI spec."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, RootModel


class MasterDerivationKeySchema(RootModel[str]):
    """MasterDerivationKey is used to derive ed25519 keys for use in wallets"""


class CreateWalletRequestSchema(BaseModel):
    """The request for `POST /v1/wallet`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    master_derivation_key: MasterDerivationKeySchema | None = Field(default=None, alias="master_derivation_key")
    wallet_driver_name: str | None = Field(default=None, alias="wallet_driver_name")
    wallet_name: str = Field(alias="wallet_name")
    wallet_password: str = Field(alias="wallet_password")


class TxTypeSchema(RootModel[str]):
    """TxType is the type of the transaction written to the ledger"""


class WalletSchema(BaseModel):
    """Wallet is the API's representation of a wallet"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    driver_name: str = Field(alias="driver_name")
    driver_version: int = Field(alias="driver_version")
    id_: str = Field(alias="id")
    mnemonic_ux: bool = Field(alias="mnemonic_ux")
    name: str = Field(alias="name")
    supported_txs: list[TxTypeSchema] = Field(alias="supported_txs")


class CreateWalletResponseSchema(BaseModel):
    """CreateWalletResponse is the response to `POST /v1/wallet`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet: WalletSchema = Field(alias="wallet")


class DeleteKeyRequestSchema(BaseModel):
    """The request for `DELETE /v1/key`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")


class DeleteMultisigRequestSchema(BaseModel):
    """The request for `DELETE /v1/multisig`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")


class DigestSchema(RootModel[str]):
    pass


class ExportKeyRequestSchema(BaseModel):
    """The request for `POST /v1/key/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")


class ExportKeyResponseSchema(BaseModel):
    """ExportKeyResponse is the response to `POST /v1/key/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    private_key: str = Field(alias="private_key")


class ExportMasterKeyRequestSchema(BaseModel):
    """The request for `POST /v1/master-key/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")


class ExportMasterKeyResponseSchema(BaseModel):
    """ExportMasterKeyResponse is the response to `POST /v1/master-key/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    master_derivation_key: MasterDerivationKeySchema = Field(alias="master_derivation_key")


class ExportMultisigRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    wallet_handle_token: str = Field(alias="wallet_handle_token")


class Ed25519PublicKeySchema(RootModel[str]):
    pass


class PublicKeySchema(RootModel[str]):
    pass


class ExportMultisigResponseSchema(BaseModel):
    """ExportMultisigResponse is the response to `POST /v1/multisig/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    multisig_version: int = Field(alias="multisig_version")
    public_keys: list[PublicKeySchema] = Field(alias="pks")
    threshold: int = Field(alias="threshold")


class GenerateKeyRequestSchema(BaseModel):
    """The request for `POST /v1/key`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(alias="wallet_handle_token")


class GenerateKeyResponseSchema(BaseModel):
    """GenerateKeyResponse is the response to `POST /v1/key`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")


class ImportKeyRequestSchema(BaseModel):
    """The request for `POST /v1/key/import`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    private_key: str = Field(alias="private_key")
    wallet_handle_token: str = Field(alias="wallet_handle_token")


class ImportKeyResponseSchema(BaseModel):
    """ImportKeyResponse is the response to `POST /v1/key/import`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")


class ImportMultisigRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/import`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    multisig_version: int = Field(alias="multisig_version")
    public_keys: list[PublicKeySchema] = Field(alias="pks")
    threshold: int = Field(alias="threshold")
    wallet_handle_token: str = Field(alias="wallet_handle_token")


class ImportMultisigResponseSchema(BaseModel):
    """ImportMultisigResponse is the response to `POST /v1/multisig/import`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")


class InitWalletHandleTokenRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/init`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_id: str = Field(alias="wallet_id")
    wallet_password: str = Field(alias="wallet_password")


class InitWalletHandleTokenResponseSchema(BaseModel):
    """InitWalletHandleTokenResponse is the response to `POST /v1/wallet/init`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(alias="wallet_handle_token")


class ListKeysRequestSchema(BaseModel):
    """The request for `POST /v1/key/list`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(alias="wallet_handle_token")


class ListKeysResponseSchema(BaseModel):
    """ListKeysResponse is the response to `POST /v1/key/list`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    addresses: list[str] = Field(alias="addresses")


class ListMultisigRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/list`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(alias="wallet_handle_token")


class ListMultisigResponseSchema(BaseModel):
    """ListMultisigResponse is the response to `POST /v1/multisig/list`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    addresses: list[str] = Field(alias="addresses")


class ListWalletsRequestSchema(BaseModel):
    """APIV1GETWalletsRequest is the request for `GET /v1/wallets`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")


class ListWalletsResponseSchema(BaseModel):
    """ListWalletsResponse is the response to `GET /v1/wallets`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallets: list[WalletSchema] = Field(alias="wallets")


class Ed25519SignatureSchema(RootModel[str]):
    pass


class SignatureSchema(RootModel[str]):
    pass


class MultisigSubsigSchema(BaseModel):
    """MultisigSubsig is a struct that holds a pair of public key and signatures
    signatures may be empty"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    public_key: PublicKeySchema = Field(alias="pk")
    signature: SignatureSchema | None = Field(default=None, alias="s")


class MultisigSigSchema(BaseModel):
    """MultisigSig is the structure that holds multiple Subsigs"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    subsignatures: list[MultisigSubsigSchema] = Field(alias="subsig")
    threshold: int = Field(alias="thr")
    version: int = Field(alias="v")


class Ed25519PrivateKeySchema(RootModel[str]):
    pass


class PrivateKeySchema(RootModel[str]):
    pass


class ReleaseWalletHandleTokenRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/release`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(alias="wallet_handle_token")


class RenameWalletRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/rename`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_id: str = Field(alias="wallet_id")
    wallet_name: str = Field(alias="wallet_name")
    wallet_password: str = Field(alias="wallet_password")


class RenameWalletResponseSchema(BaseModel):
    """RenameWalletResponse is the response to `POST /v1/wallet/rename`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet: WalletSchema = Field(alias="wallet")


class RenewWalletHandleTokenRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/renew`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(alias="wallet_handle_token")


class WalletHandleSchema(BaseModel):
    """WalletHandle includes the wallet the handle corresponds to
    and the number of number of seconds to expiratio..."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    expires_seconds: int = Field(alias="expires_seconds")
    wallet: WalletSchema = Field(alias="wallet")


class RenewWalletHandleTokenResponseSchema(BaseModel):
    """RenewWalletHandleTokenResponse is the response to `POST /v1/wallet/renew`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle: WalletHandleSchema = Field(alias="wallet_handle")


class SignMultisigResponseSchema(BaseModel):
    """SignMultisigResponse is the response to `POST /v1/multisig/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    multisig: str = Field(alias="multisig")


class SignMultisigTxnRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    partial_multisig: MultisigSigSchema | None = Field(default=None, alias="partial_multisig")
    public_key: PublicKeySchema = Field(alias="public_key")
    signer: DigestSchema | None = Field(default=None, alias="signer")
    transaction: str = Field(alias="transaction")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")


class SignProgramMultisigRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/signprogram`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    program: str = Field(alias="data")
    partial_multisig: MultisigSigSchema | None = Field(default=None, alias="partial_multisig")
    public_key: PublicKeySchema = Field(alias="public_key")
    use_legacy_msig: bool | None = Field(default=None, alias="use_legacy_msig")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")


class SignProgramMultisigResponseSchema(BaseModel):
    """SignProgramMultisigResponse is the response to `POST /v1/multisig/signdata`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    multisig: str = Field(alias="multisig")


class SignProgramRequestSchema(BaseModel):
    """The request for `POST /v1/program/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    program: str = Field(alias="data")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")


class SignProgramResponseSchema(BaseModel):
    """SignProgramResponse is the response to `POST /v1/data/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    sig: str = Field(alias="sig")


class SignTransactionResponseSchema(BaseModel):
    """SignTransactionResponse is the response to `POST /v1/transaction/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    signed_transaction: str = Field(alias="signed_transaction")


class SignTxnRequestSchema(BaseModel):
    """The request for `POST /v1/transaction/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    public_key: PublicKeySchema | None = Field(default=None, alias="public_key")
    transaction: str = Field(alias="transaction")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")


class VersionsRequestSchema(BaseModel):
    """VersionsRequest is the request for `GET /versions`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra="allow")


class VersionsResponseSchema(BaseModel):
    """VersionsResponse is the response to `GET /versions`
    friendly:VersionsResponse"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    versions: list[str] = Field(alias="versions")


class WalletInfoRequestSchema(BaseModel):
    """The request for `POST /v1/wallet/info`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle_token: str = Field(alias="wallet_handle_token")


class WalletInfoResponseSchema(BaseModel):
    """WalletInfoResponse is the response to `POST /v1/wallet/info`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    wallet_handle: WalletHandleSchema = Field(alias="wallet_handle")
