"""Generated Pydantic validation schemas."""

from .account import AccountSchema
from .accountapplicationresponse import AccountApplicationResponseSchema
from .accountassetholding import AccountAssetHoldingSchema
from .accountassetresponse import AccountAssetResponseSchema
from .accountassetsinformationresponse import AccountAssetsInformationResponseSchema
from .accountparticipation import AccountParticipationSchema
from .accountstatedelta import AccountStateDeltaSchema
from .appcalllogs import AppCallLogsSchema
from .application import ApplicationSchema
from .applicationinitialstates import ApplicationInitialStatesSchema
from .applicationkvstorage import ApplicationKVStorageSchema
from .applicationlocalreference import ApplicationLocalReferenceSchema
from .applicationlocalstate import ApplicationLocalStateSchema
from .applicationparams import ApplicationParamsSchema
from .applicationstateoperation import ApplicationStateOperationSchema
from .applicationstateschema import ApplicationStateSchemaSchema
from .asset import AssetSchema
from .assetholding import AssetHoldingSchema
from .assetholdingreference import AssetHoldingReferenceSchema
from .assetparams import AssetParamsSchema
from .avmkeyvalue import AvmKeyValueSchema
from .avmvalue import AvmValueSchema
from .blockhashresponse import BlockHashResponseSchema
from .blocklogsresponse import BlockLogsResponseSchema
from .blockresponse import BlockResponseSchema
from .blocktxidsresponse import BlockTxidsResponseSchema
from .box import BoxSchema
from .boxdescriptor import BoxDescriptorSchema
from .boxesresponse import BoxesResponseSchema
from .boxreference import BoxReferenceSchema
from .buildversion import BuildVersionSchema
from .catchpointabortresponse import CatchpointAbortResponseSchema
from .catchpointstartresponse import CatchpointStartResponseSchema
from .compileresponse import CompileResponseSchema
from .debugsettingsprof import DebugSettingsProfSchema
from .disassembleresponse import DisassembleResponseSchema
from .dryrunrequest import DryrunRequestSchema
from .dryrunresponse import DryrunResponseSchema
from .dryrunsource import DryrunSourceSchema
from .dryrunstate import DryrunStateSchema
from .dryruntxnresult import DryrunTxnResultSchema
from .errorresponse import ErrorResponseSchema
from .evaldelta import EvalDeltaSchema
from .evaldeltakeyvalue import EvalDeltaKeyValueSchema
from .genesis import GenesisSchema
from .genesisallocation import GenesisAllocationSchema
from .getblocktimestampoffsetresponse import GetBlockTimeStampOffsetResponseSchema
from .getsyncroundresponse import GetSyncRoundResponseSchema
from .ledgerstatedelta import LedgerStateDeltaSchema
from .ledgerstatedeltafortransactiongroup import LedgerStateDeltaForTransactionGroupSchema
from .lightblockheaderproof import LightBlockHeaderProofSchema
from .nodestatusresponse import NodeStatusResponseSchema
from .participationkey import ParticipationKeySchema
from .participationkeysresponse import ParticipationKeysResponseSchema
from .pendingtransactionresponse import PendingTransactionResponseSchema
from .pendingtransactionsresponse import PendingTransactionsResponseSchema
from .postparticipationresponse import PostParticipationResponseSchema
from .posttransactionsresponse import PostTransactionsResponseSchema
from .scratchchange import ScratchChangeSchema
from .simulateinitialstates import SimulateInitialStatesSchema
from .simulaterequest import SimulateRequestSchema
from .simulaterequesttransactiongroup import SimulateRequestTransactionGroupSchema
from .simulateresponse import SimulateResponseSchema
from .simulatetraceconfig import SimulateTraceConfigSchema
from .simulatetransactiongroupresult import SimulateTransactionGroupResultSchema
from .simulatetransactionresult import SimulateTransactionResultSchema
from .simulateunnamedresourcesaccessed import SimulateUnnamedResourcesAccessedSchema
from .simulationevaloverrides import SimulationEvalOverridesSchema
from .simulationopcodetraceunit import SimulationOpcodeTraceUnitSchema
from .simulationtransactionexectrace import SimulationTransactionExecTraceSchema
from .sourcemap import SourceMapSchema
from .statedelta import StateDeltaSchema
from .stateproof import StateProofSchema
from .stateproofmessage import StateProofMessageSchema
from .supplyresponse import SupplyResponseSchema
from .tealkeyvalue import TealKeyValueSchema
from .tealkeyvaluestore import TealKeyValueStoreSchema
from .tealvalue import TealValueSchema
from .transactiongroupledgerstatedeltasforroundresponse import TransactionGroupLedgerStateDeltasForRoundResponseSchema
from .transactionparametersresponse import TransactionParametersResponseSchema
from .transactionproof import TransactionProofSchema
from .version import VersionSchema

# Rebuild models to resolve forward references
AccountSchema.model_rebuild()
AccountApplicationResponseSchema.model_rebuild()
AccountAssetHoldingSchema.model_rebuild()
AccountAssetResponseSchema.model_rebuild()
AccountAssetsInformationResponseSchema.model_rebuild()
AccountParticipationSchema.model_rebuild()
AccountStateDeltaSchema.model_rebuild()
AppCallLogsSchema.model_rebuild()
ApplicationSchema.model_rebuild()
ApplicationInitialStatesSchema.model_rebuild()
ApplicationKVStorageSchema.model_rebuild()
ApplicationLocalReferenceSchema.model_rebuild()
ApplicationLocalStateSchema.model_rebuild()
ApplicationParamsSchema.model_rebuild()
ApplicationStateOperationSchema.model_rebuild()
ApplicationStateSchemaSchema.model_rebuild()
AssetSchema.model_rebuild()
AssetHoldingSchema.model_rebuild()
AssetHoldingReferenceSchema.model_rebuild()
AssetParamsSchema.model_rebuild()
AvmKeyValueSchema.model_rebuild()
AvmValueSchema.model_rebuild()
BlockHashResponseSchema.model_rebuild()
BlockLogsResponseSchema.model_rebuild()
BlockResponseSchema.model_rebuild()
BlockTxidsResponseSchema.model_rebuild()
BoxSchema.model_rebuild()
BoxDescriptorSchema.model_rebuild()
BoxReferenceSchema.model_rebuild()
BoxesResponseSchema.model_rebuild()
BuildVersionSchema.model_rebuild()
CatchpointAbortResponseSchema.model_rebuild()
CatchpointStartResponseSchema.model_rebuild()
CompileResponseSchema.model_rebuild()
DebugSettingsProfSchema.model_rebuild()
DisassembleResponseSchema.model_rebuild()
DryrunRequestSchema.model_rebuild()
DryrunResponseSchema.model_rebuild()
DryrunSourceSchema.model_rebuild()
DryrunStateSchema.model_rebuild()
DryrunTxnResultSchema.model_rebuild()
ErrorResponseSchema.model_rebuild()
EvalDeltaSchema.model_rebuild()
EvalDeltaKeyValueSchema.model_rebuild()
GenesisSchema.model_rebuild()
GenesisAllocationSchema.model_rebuild()
GetBlockTimeStampOffsetResponseSchema.model_rebuild()
GetSyncRoundResponseSchema.model_rebuild()
LedgerStateDeltaSchema.model_rebuild()
LedgerStateDeltaForTransactionGroupSchema.model_rebuild()
LightBlockHeaderProofSchema.model_rebuild()
NodeStatusResponseSchema.model_rebuild()
ParticipationKeySchema.model_rebuild()
ParticipationKeysResponseSchema.model_rebuild()
PendingTransactionResponseSchema.model_rebuild()
PendingTransactionsResponseSchema.model_rebuild()
PostParticipationResponseSchema.model_rebuild()
PostTransactionsResponseSchema.model_rebuild()
ScratchChangeSchema.model_rebuild()
SimulateInitialStatesSchema.model_rebuild()
SimulateRequestSchema.model_rebuild()
SimulateRequestTransactionGroupSchema.model_rebuild()
SimulateResponseSchema.model_rebuild()
SimulateTraceConfigSchema.model_rebuild()
SimulateTransactionGroupResultSchema.model_rebuild()
SimulateTransactionResultSchema.model_rebuild()
SimulateUnnamedResourcesAccessedSchema.model_rebuild()
SimulationEvalOverridesSchema.model_rebuild()
SimulationOpcodeTraceUnitSchema.model_rebuild()
SimulationTransactionExecTraceSchema.model_rebuild()
SourceMapSchema.model_rebuild()
StateDeltaSchema.model_rebuild()
StateProofSchema.model_rebuild()
StateProofMessageSchema.model_rebuild()
SupplyResponseSchema.model_rebuild()
TealKeyValueSchema.model_rebuild()
TealKeyValueStoreSchema.model_rebuild()
TealValueSchema.model_rebuild()
TransactionGroupLedgerStateDeltasForRoundResponseSchema.model_rebuild()
TransactionParametersResponseSchema.model_rebuild()
TransactionProofSchema.model_rebuild()
VersionSchema.model_rebuild()

__all__ = [
    "AccountApplicationResponseSchema",
    "AccountAssetHoldingSchema",
    "AccountAssetResponseSchema",
    "AccountAssetsInformationResponseSchema",
    "AccountParticipationSchema",
    "AccountSchema",
    "AccountStateDeltaSchema",
    "AppCallLogsSchema",
    "ApplicationInitialStatesSchema",
    "ApplicationKVStorageSchema",
    "ApplicationLocalReferenceSchema",
    "ApplicationLocalStateSchema",
    "ApplicationParamsSchema",
    "ApplicationSchema",
    "ApplicationStateOperationSchema",
    "ApplicationStateSchemaSchema",
    "AssetHoldingReferenceSchema",
    "AssetHoldingSchema",
    "AssetParamsSchema",
    "AssetSchema",
    "AvmKeyValueSchema",
    "AvmValueSchema",
    "BlockHashResponseSchema",
    "BlockLogsResponseSchema",
    "BlockResponseSchema",
    "BlockTxidsResponseSchema",
    "BoxDescriptorSchema",
    "BoxReferenceSchema",
    "BoxSchema",
    "BoxesResponseSchema",
    "BuildVersionSchema",
    "CatchpointAbortResponseSchema",
    "CatchpointStartResponseSchema",
    "CompileResponseSchema",
    "DebugSettingsProfSchema",
    "DisassembleResponseSchema",
    "DryrunRequestSchema",
    "DryrunResponseSchema",
    "DryrunSourceSchema",
    "DryrunStateSchema",
    "DryrunTxnResultSchema",
    "ErrorResponseSchema",
    "EvalDeltaKeyValueSchema",
    "EvalDeltaSchema",
    "GenesisAllocationSchema",
    "GenesisSchema",
    "GetBlockTimeStampOffsetResponseSchema",
    "GetSyncRoundResponseSchema",
    "LedgerStateDeltaForTransactionGroupSchema",
    "LedgerStateDeltaSchema",
    "LightBlockHeaderProofSchema",
    "NodeStatusResponseSchema",
    "ParticipationKeySchema",
    "ParticipationKeysResponseSchema",
    "PendingTransactionResponseSchema",
    "PendingTransactionsResponseSchema",
    "PostParticipationResponseSchema",
    "PostTransactionsResponseSchema",
    "ScratchChangeSchema",
    "SimulateInitialStatesSchema",
    "SimulateRequestSchema",
    "SimulateRequestTransactionGroupSchema",
    "SimulateResponseSchema",
    "SimulateTraceConfigSchema",
    "SimulateTransactionGroupResultSchema",
    "SimulateTransactionResultSchema",
    "SimulateUnnamedResourcesAccessedSchema",
    "SimulationEvalOverridesSchema",
    "SimulationOpcodeTraceUnitSchema",
    "SimulationTransactionExecTraceSchema",
    "SourceMapSchema",
    "StateDeltaSchema",
    "StateProofMessageSchema",
    "StateProofSchema",
    "SupplyResponseSchema",
    "TealKeyValueSchema",
    "TealKeyValueStoreSchema",
    "TealValueSchema",
    "TransactionGroupLedgerStateDeltasForRoundResponseSchema",
    "TransactionParametersResponseSchema",
    "TransactionProofSchema",
    "VersionSchema",
]
