# Algokit Transact Pytest Port Plan

This plan tracks every step required to mirror the TypeScript Vitest suites in
`references/algokit-core/packages/typescript/algokit_transact/tests` with
idiomatic Python/pytest equivalents under
`packages/algokit-transact/tests`.

---

## Shared Infrastructure

- [ ] Port `common.ts` loader
  - [ ] Implement JSON parsing with the same reviver semantics (bigint fields,
        `Uint8Array` → `bytes`, defaulting missing booleans/integers).
  - [ ] Produce Python `Transaction` dataclasses and related field structures
        rather than camelCase dicts.
  - [ ] Expose helpers (`get_test_vector`, `iter_transaction_cases`, etc.) that
        make per-test parametrisation trivial.
- [ ] Port `transaction_asserts.ts`
  - [ ] Implement signing/multisig helpers (ed25519, multisig merge logic).
  - [ ] Implement encode/decode assertion helpers against the Python codec.
  - [ ] Mirror error messages so expectation strings match the TS behaviour.
- [ ] Introduce reusable pytest fixtures
  - [ ] `transaction_vectors` fixture returning the parsed dataset.
  - [ ] A fixture that yields fee configuration mirrors used in TS tests.

---

## Per-Suite Porting Tasks

For every `.test.ts` file the goal is to drop the skip markers, translate the
assertions to pytest, and ensure the helper surface area exists in Python.

### `generic_transaction.test.ts` → `test_generic_transaction.py`
- [x] Enable decoding error tests (`malformed bytes`, `encode 0 bytes`).
- [x] Align raised exception types/messages with the TS expectations.

### `transaction_group.test.ts` → `test_transaction_group.py`
- [ ] Port `groupTransactions` round-trip assertions.
- [ ] Port signed transaction encode/decode loop with ed25519 signatures.
- [ ] Validate grouped transaction IDs against the shared vectors.

### `app_call.test.ts` → `test_app_call.py`
- [ ] Parametrise over the app call/create/update/delete vectors.
- [ ] Implement validation failure checks for missing programs/schema limits.
- [ ] Port successful validation/encoding cases (auth addr, multisig, etc.).
- [ ] Verify error messages match TS (`TransactionValidationError` parity).

### `asset_config.test.ts` → `test_asset_config.py`
- [ ] Port encode/decode/id assertions for create/destroy/reconfigure vectors.
- [ ] Port validation boundary tests (manager/freeze/clawback rules).

### `asset_freeze.test.ts` → `test_asset_freeze.py`
- [ ] Port freeze/unfreeze encode/decode + fee/size assertions.
- [ ] Implement validation for missing targets and frozen flag defaults.

### `asset_transfer.test.ts` → `test_asset_transfer.py`
- [ ] Port payment/opt-in/close-out encode/id/fee checks.
- [ ] Validate error paths (missing receiver, too many decimals, etc.).

### `key_registration.test.ts` → `test_key_registration.py`
- [ ] Port online/offline/non-participation vectors.
- [ ] Verify vote key dilution and lifetime validation errors.

### `payment.test.ts` → `test_payment.py`
- [ ] Port payment encode/decode/id assertions.
- [ ] Validate address/amount boundary conditions.

### `heartbeat.test.ts` → `test_heartbeat.py`
- [ ] Confirm Python implementation exposes heartbeat structures.
- [ ] Port encode/decode/validation logic once domain code is ready.

### `state_proof.test.ts` → `test_state_proof.py`
- [ ] Ensure state proof transaction support exists in Python.
- [ ] Port proof parsing/validation assertions (including reveal defaults).

---

## Finalisation

- [ ] Run the full pytest suite and compare against TS results for parity.
- [ ] Document any intentional behavioural differences (if any) in
      `README.md`.
- [ ] Remove temporary `NotImplementedError` stubs once all suites are ported.
- [ ] Add CI entry to execute the package-local pytest suites.
