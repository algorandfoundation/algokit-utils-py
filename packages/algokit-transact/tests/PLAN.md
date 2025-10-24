# Algokit Transact Pytest Port Plan

This plan tracks every step required to mirror the TypeScript Vitest suites in
`references/algokit-core/packages/typescript/algokit_transact/tests` with
idiomatic Python/pytest equivalents under
`packages/algokit-transact/tests`.

---

## Shared Infrastructure

- [ ] Port `common.ts` loader
  - [x] Implement JSON parsing with the same reviver semantics (bigint fields,
        `Uint8Array` → `bytes`, defaulting missing booleans/integers).
  - [x] Produce Python `Transaction` dataclasses and related field structures
        rather than camelCase dicts.
  - [x] Expose helpers (`get_test_vector`, `iter_transaction_cases`, etc.) that
        make per-test parametrisation trivial.
- [ ] Port `transaction_asserts.ts`
  - [x] Implement signing/multisig helpers (ed25519, multisig merge logic).
  - [x] Implement encode/decode assertion helpers against the Python codec.
  - [x] Mirror error messages so expectation strings match the TS behaviour.
- [ ] Introduce reusable pytest fixtures
  - [x] `transaction_vectors` fixture returning the parsed dataset.
  - [ ] A fixture that yields fee configuration mirrors used in TS tests.

---

## Per-Suite Porting Tasks

For every `.test.ts` file the goal is to drop the skip markers, translate the
assertions to pytest, and ensure the helper surface area exists in Python.

### `generic_transaction.test.ts` → `test_generic_transaction.py`
- [x] Enable decoding error tests (`malformed bytes`, `encode 0 bytes`).
- [x] Align raised exception types/messages with the TS expectations.

### `transaction_group.test.ts` → `test_transaction_group.py`
- [x] Port `groupTransactions` round-trip assertions.
- [x] Port signed transaction encode/decode loop with ed25519 signatures.
- [x] Validate grouped transaction IDs against the shared vectors.

### `app_call.test.ts` → `test_app_call.py`
- [x] Parametrise over the app call/create/update/delete vectors.
- [x] Implement validation failure checks for missing programs/schema limits.
- [x] Port successful validation/encoding cases (auth addr, multisig, etc.).
- [x] Verify error messages match TS (`TransactionValidationError` parity).

### `asset_config.test.ts` → `test_asset_config.py`
- [x] Port encode/decode/id assertions for create/destroy/reconfigure vectors.
- [x] Port validation boundary tests (manager/freeze/clawback rules).

### `asset_freeze.test.ts` → `test_asset_freeze.py`
- [x] Port freeze/unfreeze encode/decode + fee/size assertions.
- [x] Validate asset ID requirements mirror TS behaviour.

### `asset_transfer.test.ts` → `test_asset_transfer.py`
- [x] Port payment/opt-in/close-out encode/id/fee checks.
- [x] Validate error paths (missing receiver, too many decimals, etc.).

### `key_registration.test.ts` → `test_key_registration.py`
- [x] Port online/offline/non-participation vectors.
- [x] Verify vote key dilution and lifetime validation errors.

### `payment.test.ts` → `test_payment.py`
- [x] Port payment encode/decode/id assertions.
- [x] Validate address/amount boundary conditions.

### `heartbeat.test.ts` → `test_heartbeat.py`
- [x] Confirm Python implementation exposes heartbeat structures.
- [x] Port encode/decode/validation logic once domain code is ready.

### `state_proof.test.ts` → `test_state_proof.py`
- [x] Ensure state proof transaction support exists in Python.
- [x] Port proof parsing/validation assertions (including reveal defaults).

---

## Finalisation

- [ ] Run the full pytest suite and compare against TS results for parity.
- [ ] Document any intentional behavioural differences (if any) in
      `README.md`.
- [ ] Remove temporary `NotImplementedError` stubs once all suites are ported.
- [ ] Add CI entry to execute the package-local pytest suites.
