"""Generated Pydantic validation schemas."""

from .createwalletrequest import CreateWalletRequestSchema
from .createwalletresponse import CreateWalletResponseSchema
from .deletekeyrequest import DeleteKeyRequestSchema
from .deletemultisigrequest import DeleteMultisigRequestSchema
from .digest import DigestSchema
from .ed25519privatekey import ed25519PrivateKeySchema
from .ed25519publickey import ed25519PublicKeySchema
from .ed25519signature import ed25519SignatureSchema
from .exportkeyrequest import ExportKeyRequestSchema
from .exportkeyresponse import ExportKeyResponseSchema
from .exportmasterkeyrequest import ExportMasterKeyRequestSchema
from .exportmasterkeyresponse import ExportMasterKeyResponseSchema
from .exportmultisigrequest import ExportMultisigRequestSchema
from .exportmultisigresponse import ExportMultisigResponseSchema
from .generatekeyrequest import GenerateKeyRequestSchema
from .generatekeyresponse import GenerateKeyResponseSchema
from .importkeyrequest import ImportKeyRequestSchema
from .importkeyresponse import ImportKeyResponseSchema
from .importmultisigrequest import ImportMultisigRequestSchema
from .importmultisigresponse import ImportMultisigResponseSchema
from .initwallethandletokenrequest import InitWalletHandleTokenRequestSchema
from .initwallethandletokenresponse import InitWalletHandleTokenResponseSchema
from .listkeysrequest import ListKeysRequestSchema
from .listkeysresponse import ListKeysResponseSchema
from .listmultisigrequest import ListMultisigRequestSchema
from .listmultisigresponse import ListMultisigResponseSchema
from .listwalletsrequest import ListWalletsRequestSchema
from .listwalletsresponse import ListWalletsResponseSchema
from .masterderivationkey import MasterDerivationKeySchema
from .multisigsig import MultisigSigSchema
from .multisigsubsig import MultisigSubsigSchema
from .privatekey import PrivateKeySchema
from .publickey import PublicKeySchema
from .releasewallethandletokenrequest import ReleaseWalletHandleTokenRequestSchema
from .renamewalletrequest import RenameWalletRequestSchema
from .renamewalletresponse import RenameWalletResponseSchema
from .renewwallethandletokenrequest import RenewWalletHandleTokenRequestSchema
from .renewwallethandletokenresponse import RenewWalletHandleTokenResponseSchema
from .signature import SignatureSchema
from .signmultisigresponse import SignMultisigResponseSchema
from .signmultisigtxnrequest import SignMultisigTxnRequestSchema
from .signprogrammultisigrequest import SignProgramMultisigRequestSchema
from .signprogrammultisigresponse import SignProgramMultisigResponseSchema
from .signprogramrequest import SignProgramRequestSchema
from .signprogramresponse import SignProgramResponseSchema
from .signtransactionresponse import SignTransactionResponseSchema
from .signtxnrequest import SignTxnRequestSchema
from .txtype import TxTypeSchema
from .versionsrequest import VersionsRequestSchema
from .versionsresponse import VersionsResponseSchema
from .wallet import WalletSchema
from .wallethandle import WalletHandleSchema
from .walletinforequest import WalletInfoRequestSchema
from .walletinforesponse import WalletInfoResponseSchema

# Rebuild models to resolve forward references
CreateWalletRequestSchema.model_rebuild()
CreateWalletResponseSchema.model_rebuild()
DeleteKeyRequestSchema.model_rebuild()
DeleteMultisigRequestSchema.model_rebuild()
DigestSchema.model_rebuild()
ExportKeyRequestSchema.model_rebuild()
ExportKeyResponseSchema.model_rebuild()
ExportMasterKeyRequestSchema.model_rebuild()
ExportMasterKeyResponseSchema.model_rebuild()
ExportMultisigRequestSchema.model_rebuild()
ExportMultisigResponseSchema.model_rebuild()
GenerateKeyRequestSchema.model_rebuild()
GenerateKeyResponseSchema.model_rebuild()
ImportKeyRequestSchema.model_rebuild()
ImportKeyResponseSchema.model_rebuild()
ImportMultisigRequestSchema.model_rebuild()
ImportMultisigResponseSchema.model_rebuild()
InitWalletHandleTokenRequestSchema.model_rebuild()
InitWalletHandleTokenResponseSchema.model_rebuild()
ListKeysRequestSchema.model_rebuild()
ListKeysResponseSchema.model_rebuild()
ListMultisigRequestSchema.model_rebuild()
ListMultisigResponseSchema.model_rebuild()
ListWalletsRequestSchema.model_rebuild()
ListWalletsResponseSchema.model_rebuild()
MasterDerivationKeySchema.model_rebuild()
MultisigSigSchema.model_rebuild()
MultisigSubsigSchema.model_rebuild()
PrivateKeySchema.model_rebuild()
PublicKeySchema.model_rebuild()
ReleaseWalletHandleTokenRequestSchema.model_rebuild()
RenameWalletRequestSchema.model_rebuild()
RenameWalletResponseSchema.model_rebuild()
RenewWalletHandleTokenRequestSchema.model_rebuild()
RenewWalletHandleTokenResponseSchema.model_rebuild()
SignMultisigResponseSchema.model_rebuild()
SignMultisigTxnRequestSchema.model_rebuild()
SignProgramMultisigRequestSchema.model_rebuild()
SignProgramMultisigResponseSchema.model_rebuild()
SignProgramRequestSchema.model_rebuild()
SignProgramResponseSchema.model_rebuild()
SignTransactionResponseSchema.model_rebuild()
SignTxnRequestSchema.model_rebuild()
SignatureSchema.model_rebuild()
TxTypeSchema.model_rebuild()
VersionsRequestSchema.model_rebuild()
VersionsResponseSchema.model_rebuild()
WalletSchema.model_rebuild()
WalletHandleSchema.model_rebuild()
WalletInfoRequestSchema.model_rebuild()
WalletInfoResponseSchema.model_rebuild()
ed25519PrivateKeySchema.model_rebuild()
ed25519PublicKeySchema.model_rebuild()
ed25519SignatureSchema.model_rebuild()

__all__ = [
    "CreateWalletRequestSchema",
    "CreateWalletResponseSchema",
    "DeleteKeyRequestSchema",
    "DeleteMultisigRequestSchema",
    "DigestSchema",
    "ExportKeyRequestSchema",
    "ExportKeyResponseSchema",
    "ExportMasterKeyRequestSchema",
    "ExportMasterKeyResponseSchema",
    "ExportMultisigRequestSchema",
    "ExportMultisigResponseSchema",
    "GenerateKeyRequestSchema",
    "GenerateKeyResponseSchema",
    "ImportKeyRequestSchema",
    "ImportKeyResponseSchema",
    "ImportMultisigRequestSchema",
    "ImportMultisigResponseSchema",
    "InitWalletHandleTokenRequestSchema",
    "InitWalletHandleTokenResponseSchema",
    "ListKeysRequestSchema",
    "ListKeysResponseSchema",
    "ListMultisigRequestSchema",
    "ListMultisigResponseSchema",
    "ListWalletsRequestSchema",
    "ListWalletsResponseSchema",
    "MasterDerivationKeySchema",
    "MultisigSigSchema",
    "MultisigSubsigSchema",
    "PrivateKeySchema",
    "PublicKeySchema",
    "ReleaseWalletHandleTokenRequestSchema",
    "RenameWalletRequestSchema",
    "RenameWalletResponseSchema",
    "RenewWalletHandleTokenRequestSchema",
    "RenewWalletHandleTokenResponseSchema",
    "SignMultisigResponseSchema",
    "SignMultisigTxnRequestSchema",
    "SignProgramMultisigRequestSchema",
    "SignProgramMultisigResponseSchema",
    "SignProgramRequestSchema",
    "SignProgramResponseSchema",
    "SignTransactionResponseSchema",
    "SignTxnRequestSchema",
    "SignatureSchema",
    "TxTypeSchema",
    "VersionsRequestSchema",
    "VersionsResponseSchema",
    "WalletHandleSchema",
    "WalletInfoRequestSchema",
    "WalletInfoResponseSchema",
    "WalletSchema",
    "ed25519PrivateKeySchema",
    "ed25519PublicKeySchema",
    "ed25519SignatureSchema",
]
