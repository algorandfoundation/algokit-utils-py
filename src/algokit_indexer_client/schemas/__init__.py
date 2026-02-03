"""Generated Pydantic validation schemas."""

from .account import AccountSchema
from .accountparticipation import AccountParticipationSchema
from .accountresponse import AccountResponseSchema
from .accountsresponse import AccountsResponseSchema
from .accountstatedelta import AccountStateDeltaSchema
from .application import ApplicationSchema
from .applicationlocalstate import ApplicationLocalStateSchema
from .applicationlocalstatesresponse import ApplicationLocalStatesResponseSchema
from .applicationlogdata import ApplicationLogDataSchema
from .applicationlogsresponse import ApplicationLogsResponseSchema
from .applicationparams import ApplicationParamsSchema
from .applicationresponse import ApplicationResponseSchema
from .applicationsresponse import ApplicationsResponseSchema
from .applicationstateschema import ApplicationStateSchemaSchema
from .asset import AssetSchema
from .assetbalancesresponse import AssetBalancesResponseSchema
from .assetholding import AssetHoldingSchema
from .assetholdingsresponse import AssetHoldingsResponseSchema
from .assetparams import AssetParamsSchema
from .assetresponse import AssetResponseSchema
from .assetsresponse import AssetsResponseSchema
from .block import BlockSchema
from .blockheadersresponse import BlockHeadersResponseSchema
from .blockrewards import BlockRewardsSchema
from .blockupgradestate import BlockUpgradeStateSchema
from .blockupgradevote import BlockUpgradeVoteSchema
from .box import BoxSchema
from .boxdescriptor import BoxDescriptorSchema
from .boxesresponse import BoxesResponseSchema
from .boxreference import BoxReferenceSchema
from .errorresponse import ErrorResponseSchema
from .evaldelta import EvalDeltaSchema
from .evaldeltakeyvalue import EvalDeltaKeyValueSchema
from .hashfactory import HashFactorySchema
from .hashtype import HashtypeSchema
from .hbprooffields import HbProofFieldsSchema
from .healthcheck import HealthCheckSchema
from .holdingref import HoldingRefSchema
from .indexerstateproofmessage import IndexerStateProofMessageSchema
from .localsref import LocalsRefSchema
from .merklearrayproof import MerkleArrayProofSchema
from .miniassetholding import MiniAssetHoldingSchema
from .oncompletion import OnCompletionSchema
from .participationupdates import ParticipationUpdatesSchema
from .resourceref import ResourceRefSchema
from .statedelta import StateDeltaSchema
from .stateprooffields import StateProofFieldsSchema
from .stateproofparticipant import StateProofParticipantSchema
from .stateproofreveal import StateProofRevealSchema
from .stateproofsignature import StateProofSignatureSchema
from .stateproofsigslot import StateProofSigSlotSchema
from .stateprooftracking import StateProofTrackingSchema
from .stateproofverifier import StateProofVerifierSchema
from .stateschema import StateSchemaSchema
from .tealkeyvalue import TealKeyValueSchema
from .tealkeyvaluestore import TealKeyValueStoreSchema
from .tealvalue import TealValueSchema
from .transaction import TransactionSchema
from .transactionapplication import TransactionApplicationSchema
from .transactionassetconfig import TransactionAssetConfigSchema
from .transactionassetfreeze import TransactionAssetFreezeSchema
from .transactionassettransfer import TransactionAssetTransferSchema
from .transactionheartbeat import TransactionHeartbeatSchema
from .transactionkeyreg import TransactionKeyregSchema
from .transactionpayment import TransactionPaymentSchema
from .transactionresponse import TransactionResponseSchema
from .transactionsignature import TransactionSignatureSchema
from .transactionsignaturelogicsig import TransactionSignatureLogicsigSchema
from .transactionsignaturemultisig import TransactionSignatureMultisigSchema
from .transactionsignaturemultisigsubsignature import TransactionSignatureMultisigSubsignatureSchema
from .transactionsresponse import TransactionsResponseSchema
from .transactionstateproof import TransactionStateProofSchema

# Rebuild models to resolve forward references
AccountSchema.model_rebuild()
AccountParticipationSchema.model_rebuild()
AccountResponseSchema.model_rebuild()
AccountStateDeltaSchema.model_rebuild()
AccountsResponseSchema.model_rebuild()
ApplicationSchema.model_rebuild()
ApplicationLocalStateSchema.model_rebuild()
ApplicationLocalStatesResponseSchema.model_rebuild()
ApplicationLogDataSchema.model_rebuild()
ApplicationLogsResponseSchema.model_rebuild()
ApplicationParamsSchema.model_rebuild()
ApplicationResponseSchema.model_rebuild()
ApplicationStateSchemaSchema.model_rebuild()
ApplicationsResponseSchema.model_rebuild()
AssetSchema.model_rebuild()
AssetBalancesResponseSchema.model_rebuild()
AssetHoldingSchema.model_rebuild()
AssetHoldingsResponseSchema.model_rebuild()
AssetParamsSchema.model_rebuild()
AssetResponseSchema.model_rebuild()
AssetsResponseSchema.model_rebuild()
BlockSchema.model_rebuild()
BlockHeadersResponseSchema.model_rebuild()
BlockRewardsSchema.model_rebuild()
BlockUpgradeStateSchema.model_rebuild()
BlockUpgradeVoteSchema.model_rebuild()
BoxSchema.model_rebuild()
BoxDescriptorSchema.model_rebuild()
BoxReferenceSchema.model_rebuild()
BoxesResponseSchema.model_rebuild()
ErrorResponseSchema.model_rebuild()
EvalDeltaSchema.model_rebuild()
EvalDeltaKeyValueSchema.model_rebuild()
HashFactorySchema.model_rebuild()
HashtypeSchema.model_rebuild()
HbProofFieldsSchema.model_rebuild()
HealthCheckSchema.model_rebuild()
HoldingRefSchema.model_rebuild()
IndexerStateProofMessageSchema.model_rebuild()
LocalsRefSchema.model_rebuild()
MerkleArrayProofSchema.model_rebuild()
MiniAssetHoldingSchema.model_rebuild()
OnCompletionSchema.model_rebuild()
ParticipationUpdatesSchema.model_rebuild()
ResourceRefSchema.model_rebuild()
StateDeltaSchema.model_rebuild()
StateProofFieldsSchema.model_rebuild()
StateProofParticipantSchema.model_rebuild()
StateProofRevealSchema.model_rebuild()
StateProofSigSlotSchema.model_rebuild()
StateProofSignatureSchema.model_rebuild()
StateProofTrackingSchema.model_rebuild()
StateProofVerifierSchema.model_rebuild()
StateSchemaSchema.model_rebuild()
TealKeyValueSchema.model_rebuild()
TealKeyValueStoreSchema.model_rebuild()
TealValueSchema.model_rebuild()
TransactionSchema.model_rebuild()
TransactionApplicationSchema.model_rebuild()
TransactionAssetConfigSchema.model_rebuild()
TransactionAssetFreezeSchema.model_rebuild()
TransactionAssetTransferSchema.model_rebuild()
TransactionHeartbeatSchema.model_rebuild()
TransactionKeyregSchema.model_rebuild()
TransactionPaymentSchema.model_rebuild()
TransactionResponseSchema.model_rebuild()
TransactionSignatureSchema.model_rebuild()
TransactionSignatureLogicsigSchema.model_rebuild()
TransactionSignatureMultisigSchema.model_rebuild()
TransactionSignatureMultisigSubsignatureSchema.model_rebuild()
TransactionStateProofSchema.model_rebuild()
TransactionsResponseSchema.model_rebuild()

__all__ = [
    "AccountParticipationSchema",
    "AccountResponseSchema",
    "AccountSchema",
    "AccountStateDeltaSchema",
    "AccountsResponseSchema",
    "ApplicationLocalStateSchema",
    "ApplicationLocalStatesResponseSchema",
    "ApplicationLogDataSchema",
    "ApplicationLogsResponseSchema",
    "ApplicationParamsSchema",
    "ApplicationResponseSchema",
    "ApplicationSchema",
    "ApplicationStateSchemaSchema",
    "ApplicationsResponseSchema",
    "AssetBalancesResponseSchema",
    "AssetHoldingSchema",
    "AssetHoldingsResponseSchema",
    "AssetParamsSchema",
    "AssetResponseSchema",
    "AssetSchema",
    "AssetsResponseSchema",
    "BlockHeadersResponseSchema",
    "BlockRewardsSchema",
    "BlockSchema",
    "BlockUpgradeStateSchema",
    "BlockUpgradeVoteSchema",
    "BoxDescriptorSchema",
    "BoxReferenceSchema",
    "BoxSchema",
    "BoxesResponseSchema",
    "ErrorResponseSchema",
    "EvalDeltaKeyValueSchema",
    "EvalDeltaSchema",
    "HashFactorySchema",
    "HashtypeSchema",
    "HbProofFieldsSchema",
    "HealthCheckSchema",
    "HoldingRefSchema",
    "IndexerStateProofMessageSchema",
    "LocalsRefSchema",
    "MerkleArrayProofSchema",
    "MiniAssetHoldingSchema",
    "OnCompletionSchema",
    "ParticipationUpdatesSchema",
    "ResourceRefSchema",
    "StateDeltaSchema",
    "StateProofFieldsSchema",
    "StateProofParticipantSchema",
    "StateProofRevealSchema",
    "StateProofSigSlotSchema",
    "StateProofSignatureSchema",
    "StateProofTrackingSchema",
    "StateProofVerifierSchema",
    "StateSchemaSchema",
    "TealKeyValueSchema",
    "TealKeyValueStoreSchema",
    "TealValueSchema",
    "TransactionApplicationSchema",
    "TransactionAssetConfigSchema",
    "TransactionAssetFreezeSchema",
    "TransactionAssetTransferSchema",
    "TransactionHeartbeatSchema",
    "TransactionKeyregSchema",
    "TransactionPaymentSchema",
    "TransactionResponseSchema",
    "TransactionSchema",
    "TransactionSignatureLogicsigSchema",
    "TransactionSignatureMultisigSchema",
    "TransactionSignatureMultisigSubsignatureSchema",
    "TransactionSignatureSchema",
    "TransactionStateProofSchema",
    "TransactionsResponseSchema",
]
