# Migration Notes

A collection of notes to consolidate todos during decoupling efforts (similar doc exists on ts version as well).

## API

### Generator

- Currently generated models for KMD have explicit request models resulting in slightly different signatures in contrast with indexer and algod and requiring imports of explicit typed request models specifically on kmd client calls. Do we want to further refine the generation to auto flatten the keys to ensure it does not define an explicit request models or change those models to TypedDicts to reduce the import overhead?

### Algod OAS

is_frozen field on models in algod is a boolean in the spec but actual returning value is an integer, serde must be updated to handle casting to bool.

### KMD

- algokit-core repo on a branch called feat/account-manager, we had a minor refinement in OAS spec for kmd adding a default value for wallet driver field as well as the generator adjustments to ensure generated model for related endpoint falls back to default 'sqlite' value. Do we want to restore this approach?:

### Type annotations

- Type hints and documentation now refer to the generated `algokit_algod_client.AlgodClient` (instead of `algosdk.v2client.algod.AlgodClient`). Update any downstream annotations or typing imports accordingly when migrating to v4.
