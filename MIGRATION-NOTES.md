# Migration Notes

A collection of notes to consolidate todos during decoupling efforts (similar doc exists on ts version as well).

## API Generator

- Currently generated models for KMD have explicit request models resulting in slightly different signatures in contrast with indexer and algod and requiring imports of explicit typed request models specifically on kmd client calls. Do we want to further refine the generation to auto flatten the keys to ensure it does not define an explicit request models or change those models to TypedDicts to reduce the import overhead?
