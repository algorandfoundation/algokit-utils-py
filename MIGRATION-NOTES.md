# MIGRATION NOTES

A collection of notes that surfaced while aligning the Python composer with the latest TypeScript decoupling work.

- `TransactionComposer.add_atc` has been removed; composer groups can no longer ingest pre-built `AtomicTransactionComposer` instances.
- TODO: port access list handling into `populate_group_resource` / method-call builders so `use_access_list` stops being a no-op.
- TODO: review the `TODO: PD - review this way of assigning fee` branch when assigning additional fees during coverage; confirm behaviour matches the TS composer.
- TODO: restore support for injecting pre-built ATCs once parity decisions are final (or document the breaking change clearly).
- TODO: audit error transformation so the Python layer mirrors the new SDK error surfaces (e.g. nested simulate failures).
- TODO: document the new `FeeDelta` / `FeePriority` wrappers and ensure public typing matches the TS migration guidance.
- TODO: re-enable deterministic resource-order testing once resource-population parity is confirmed.
- TODO: update downstream packages (tests, docs, code examples) that reference legacy composer behaviour removed during this refactor.
