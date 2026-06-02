# PRD: AccountManager.fromSecret with Simplified Wrapped Interfaces

## Problem Statement

The Python algokit-utils library currently has a fragmented interface for creating accounts from secrets:

1. **`from_mnemonic`** only supports legacy 25-word Algorand mnemonics, requiring the mnemonic to be passed as a plain string
2. **Wrapped secret interfaces** require mandatory `wrap_*` methods, which is cumbersome for implementations where wrapping is handled automatically (e.g., hardware wallets, certain keyring services)
3. **No unified `fromSecret` method** exists that can accept multiple secret types (seeds, HD extended keys, HD mnemonics, legacy mnemonics) through a single ergonomic interface
4. Users working with **HD wallets** must manually convert mnemonics to seeds and then derive keys, rather than having a direct path from wrapped mnemonics to accounts

This creates friction for developers who want to:
- Use secure key storage with wrapped secrets that don't need explicit re-wrapping
- Work with HD wallets using BIP39 mnemonics
- Have a single consistent interface for all secret types

## Solution

Implement a unified `from_secret` method on `AccountManager` that accepts any wrapped secret type (Ed25519 seed, HD extended private key, HD mnemonic, or legacy mnemonic). Simplify the wrapped secret interfaces by making the `wrap` method optional. Deprecate `from_mnemonic` in favor of `from_secret`.

This mirrors the TypeScript PR #575 and brings the Python library into parity with the TypeScript implementation's ergonomics.

## User Stories

1. As a developer using a hardware wallet, I want to pass a wrapped secret without implementing a no-op wrap method, so that my code is cleaner and more focused on the actual security requirements.

2. As a developer using HD wallets with BIP39 mnemonics, I want to create an account directly from a wrapped HD mnemonic, so that I don't have to manually convert the mnemonic to a seed and derive the account.

3. As a developer migrating from the TypeScript algokit-utils, I want the same `fromSecret` interface in Python, so that I can maintain consistency across my codebase.

4. As a developer using secure key storage, I want to use wrapped secrets for all account types (seeds, HD keys, and mnemonics), so that my private key material is never exposed in plaintext.

5. As a developer working with legacy Algorand accounts, I want to continue using 25-word mnemonics through the new `from_secret` interface, so that I can migrate to the new API without losing existing functionality.

6. As a developer reviewing code, I want to see a single `from_secret` method used consistently across the codebase, so that I can more easily understand and audit secret handling.

7. As a security-conscious developer, I want the `wrap` method to be optional in wrapped secret protocols, so that implementations where secrets are automatically secured don't require boilerplate code.

8. As a developer working with the AlgorandClient, I want to call `algorand.account.from_secret()` with any wrapped secret type, so that I can create and register accounts in a single, consistent call.

9. As a maintainer of the library, I want to deprecate `from_mnemonic` with a clear migration path, so that users gradually move to the more secure and flexible `from_secret` method.

10. As a developer writing tests, I want to mock wrapped secrets without implementing wrap methods, so that my test code is simpler and more maintainable.

## Implementation Decisions

### Module Structure

The implementation spans two primary modules:

1. **`algokit_crypto`** - Contains the wrapped secret protocols and signing key derivation functions
2. **`algokit_utils.accounts`** - Contains the `AccountManager` class with the new `from_secret` method

### Wrapped Secret Protocol Changes

**Current State:**
- `WrappedEd25519Seed` requires `wrap_ed25519_seed()` method
- `WrappedHdExtendedPrivateKey` requires `wrap_hd_extended_private_key()` method

**New State:**
- `WrappedEd25519Seed` with `unwrap_ed25519_seed()` and optional `wrap()` method
- `WrappedHdExtendedPrivateKey` with `unwrap_hd_extended_private_key()` and optional `wrap()` method
- `WrappedHdMnemonic` (new) with `unwrap_hd_mnemonic()` and optional `wrap()` method
- `WrappedLegacyMnemonic` (new) with `unwrap_legacy_mnemonic()` and optional `wrap()` method

**Type Union:**
```python
WrappedEd25519Secret = (
    WrappedEd25519Seed 
    | WrappedHdExtendedPrivateKey 
    | WrappedHdMnemonic 
    | WrappedLegacyMnemonic
)
```

### HD Wallet Helper Functions

Three new helper functions will be added to support HD mnemonic handling:

1. `hd_seed_from_mnemonic(mnemonic: str) -> bytearray` - Converts BIP39 mnemonic to 64-byte seed using xhd-wallet-api's `seed_from_mnemonic`
2. `hd_root_key_from_seed(seed: bytearray) -> bytearray` - Converts seed to 96-byte extended private key root
3. `hd_root_key_from_mnemonic(mnemonic: str) -> bytearray` - Combines the above two functions

### Signing Key Derivation Updates

The `ed25519_signing_key_from_wrapped_secret` function will be updated to handle all four wrapped secret types:

- **WrappedEd25519Seed**: Use PyNaCl to derive public key and create signer
- **WrappedHdExtendedPrivateKey**: Use xhd-wallet-api to derive public key and create raw signer
- **WrappedHdMnemonic**: Convert to seed → root key → derive account 0, index 0 → create signer
- **WrappedLegacyMnemonic**: Convert to 32-byte seed using algo25 → use PyNaCl for signing

### AccountManager.from_secret Method

```python
def from_secret(
    self,
    *,
    secret: WrappedEd25519Secret,
    sender: str | None = None
) -> AddressWithSigners:
    """Create and register an account from a wrapped secret.
    
    Supports Ed25519 seeds, HD extended private keys, HD mnemonics (BIP39),
    and legacy Algorand mnemonics (25-word).
    
    Args:
        secret: A wrapped secret implementing one of the WrappedEd25519Secret protocols
        sender: Optional sender address for rekeyed accounts
        
    Returns:
        AddressWithSigners: The created account with signer registered
    """
```

### Deprecation Strategy

`from_mnemonic` will be marked as deprecated using Python's `warnings` module with `DeprecationWarning`. The deprecation message will direct users to use `from_secret` with `WrappedLegacyMnemonic` instead.

### Error Handling

All wrapped secret operations will maintain the existing error handling patterns:
- Invalid secret lengths raise `ValueError`
- Failures during unwrap/sign/wrap operations raise `ExceptionGroup` when both operations fail
- Secret zeroing happens in `finally` blocks to ensure memory cleanup

## Testing Decisions

### Test Philosophy

Tests should focus on external behavior (public API contracts) rather than implementation details. Specifically:

- Test that `from_secret` correctly creates accounts for each secret type
- Test that optional `wrap` methods are truly optional (can be omitted)
- Test deprecation warnings are raised for `from_mnemonic`
- Test error handling paths (invalid secrets, wrap failures)
- Test integration with `AlgorandClient` via `set_signer_from_account`

### Test Modules

1. **`tests/crypto/test_wrapped_secrets.py`** - Unit tests for wrapped secret protocols and signing key derivation
2. **`tests/accounts/test_account_manager.py`** - Integration tests for `from_secret` method

### Prior Art

Similar tests exist for:
- `ed25519_signing_key_from_wrapped_secret` in `tests/modules/crypto/test_signing.py`
- `from_mnemonic` in `tests/accounts/test_account_manager.py`
- Keyring examples in `examples/signing/`

## Out of Scope

The following are explicitly out of scope for this PRD:

1. **Moving algo25 under crypto** - The TypeScript PR moved algo25 under the crypto package to avoid circular dependencies. This is not needed in Python as algo25 is already a separate package.

2. **Adding passphrase support for HD mnemonics** - The HD mnemonic functions will use empty passphrases by default. Support for custom passphrases can be added in a future iteration.

3. **Custom derivation paths for HD mnemonics** - HD mnemonics will always derive account 0, index 0. Users needing custom paths can use `WrappedHdExtendedPrivateKey` directly.

4. **Async wrapped secrets** - The Python implementation uses synchronous protocols. Async support is not needed at this time.

5. **Documentation updates** - While the implementation will include docstrings, updating the external documentation site is out of scope.

## Further Notes

### Breaking Changes

This is a **breaking change** (hence `feat!:` in the commit type):

1. The `wrap` method becoming optional changes the Protocol definition, which could affect existing implementations that relied on the method being required (though runtime behavior remains compatible)

2. `from_mnemonic` is deprecated, though it will continue to work until the next major version

### TypeScript Parity

This implementation aims to match the TypeScript PR #575 behavior:
- Same wrapped secret type names
- Same method signatures (adapted to Python conventions)
- Same optional `wrap` function pattern
- Same `fromSecret` method signature

### Security Considerations

- All secrets are zeroed in memory after use via `finally` blocks
- The optional `wrap` method design reduces friction for secure implementations while still supporting explicit wrapping when needed
- Mnemonic-to-seed conversion happens in memory and the seed is not retained after account creation

### Migration Path for Users

Users currently using `from_mnemonic` can migrate as follows:

**Before:**
```python
account = account_manager.from_mnemonic(mnemonic="word1 word2 ...")
```

**After:**
```python
class WrappedMnemonic:
    def __init__(self, mnemonic: str):
        self._mnemonic = mnemonic
    def unwrap_legacy_mnemonic(self) -> str:
        return self._mnemonic

account = account_manager.from_secret(secret=WrappedMnemonic("word1 word2 ..."))
```

Or for simpler cases, a convenience wrapper can be provided in the future.
