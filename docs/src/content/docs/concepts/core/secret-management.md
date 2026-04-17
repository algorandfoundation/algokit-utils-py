---
title: Secret management
description: AlgoKit utils provides interfaces and concrete functions to enable secure management of secret material for signing transactions. This includes support for using an external KMS or key wrapping and unwrapping with a secrets manager.
---

In general, there are three levels of security when it comes to signing transactions with secret material:

1. KMS - The secret material is never exposed to the application
1. Key Wrapping and Unwrapping - The secret material is stored outside of the app (i.e. keychain) and only loaded in memory when signing
1. Plaintext - The secret material is stored in plaintext (i.e. in the environment) and is accessible throughout the runtime of the application

While using plaintext environment variables may be the easier to setup, it is **not recommended** for production use. A compromised environment and/or dependency could lead to the secret material being compromised. Additionally, it is easy to accidentally leak secrets in plaintext through git commits.

The most secure option is to use an external KMS that completely isolates the secret material from the application. KMS', however, can have a high setup cost which may be difficult for a solo developer or small team to manage properly. In this case, the next recommended option is to use key wrapping and unwrapping with a secrets manager. This allows the secret material to be stored securely outside of the application and only loaded in memory when signing is necessary. For example, on a local machine, the OS keyring can be used to store the secret material and only load it when signing transactions.

## Signing with a Wrapped Secret

### Using Keyring Secrets

To read a mnemonic from the OS keyring, you can use the `keyring` library. This prevents the mnemonic from being stored in
plaintext and ensures it is only loaded in memory when signing.

#### Ed25519 Seed or Mnemonic

When working with a ed25519 seed or mnemonic, you can implement the `WrappedEd25519Seed` interface which allows you to wrap and unwrap the seed as needed. For example, with `keyring`:

```python
import keyring

from algokit_algo25 import seed_from_mnemonic
from algokit_crypto import WrappedEd25519Seed, ed25519_signing_key_from_wrapped_secret
from algokit_transact import generate_address_with_signers
from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams

MNEMONIC_NAME = "algorand-mainnet-mnemonic"


class KeyringWrappedSeed(WrappedEd25519Seed):
    def unwrap_ed25519_seed(self) -> bytearray:
        mnemonic = keyring.get_password("algorand", MNEMONIC_NAME)
        if mnemonic is None:
            raise ValueError(f"No mnemonic found in keyring for {MNEMONIC_NAME}")
        return bytearray(seed_from_mnemonic(mnemonic))

    def wrap_ed25519_seed(self) -> None:
        pass


wrapped_seed = KeyringWrappedSeed()
signing_key = ed25519_signing_key_from_wrapped_secret(wrapped_seed)
algorand_account = generate_address_with_signers(
    signing_key["ed25519_pubkey"],
    signing_key["raw_ed25519_signer"],
)

algorand = AlgorandClient.default_localnet()

algorand.account.ensure_funded_from_environment(algorand_account.addr, AlgoAmount.from_algo(1))
algorand.set_signer_from_account(algorand_account)

algorand.send.payment(
    PaymentParams(
        sender=algorand_account.addr,
        receiver=algorand_account.addr,
        amount=AlgoAmount.from_micro_algo(0),
    )
)
```

### HD Expanded Secret Key

HD accounts have a 96-byte expanded secret key that can be used in a similar manner to the ed25519 seed, except we need to implement the `WrappedHdExtendedPrivateKey` interface. For example, with `keyring`:

```python
import base64

import keyring

from algokit_crypto import (
    WrappedHdExtendedPrivateKey,
    ed25519_signing_key_from_wrapped_secret,
)
from algokit_transact import generate_address_with_signers
from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams

SECRET_NAME = "algorand-hd-extended-key"


class KeyringWrappedHdKey(WrappedHdExtendedPrivateKey):
    def unwrap_hd_extended_private_key(self) -> bytearray:
        secret_b64 = keyring.get_password("algorand", SECRET_NAME)
        if secret_b64 is None:
            raise ValueError(f"No HD key found in keyring for {SECRET_NAME}")

        esk = bytearray(base64.b64decode(secret_b64))

        # The last 32 bytes of the extended private key is the chain code, which is not
        # needed for signing. This means in most cases you can just store the first 64
        # bytes and then pad the secret to 96 bytes in the unwrap function. If you are
        # storing the full 96 bytes, you can just return the secret as is.
        if len(esk) == 64:
            padded = bytearray(96)
            padded[:64] = esk
            return padded

        return esk

    def wrap_hd_extended_private_key(self) -> None:
        pass


wrapped_key = KeyringWrappedHdKey()
signing_key = ed25519_signing_key_from_wrapped_secret(wrapped_key)
algorand_account = generate_address_with_signers(
    signing_key["ed25519_pubkey"],
    signing_key["raw_ed25519_signer"],
)

algorand = AlgorandClient.default_localnet()

algorand.account.ensure_funded_from_environment(algorand_account.addr, AlgoAmount.from_algo(1))
algorand.set_signer_from_account(algorand_account)

algorand.send.payment(
    PaymentParams(
        sender=algorand_account.addr,
        receiver=algorand_account.addr,
        amount=AlgoAmount.from_micro_algo(0),
    )
)
```

## Signing with a KMS

### Note on KMS Authentication in CI

If you are using a KMS in CI, the best practice for performing signing operations is to use OIDC. For guides for setting up OIDC, refer to the [GitHub documentation](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments).

### Signing with AWS KMS

Using the KMS, you can retrieve the public key and implement a `raw_ed25519_signer` callback which can then be used to generate an Algorand address and all Algorand-specific signing functions. For example, with AWS:

```python
import os

import boto3

from algokit_transact import generate_address_with_signers
from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams

# The following environment variables must be set for this to work:
# - AWS_REGION
# - KEY_ID
# - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
kms = boto3.client("kms", region_name=os.environ["AWS_REGION"])
key_id = os.environ["KEY_ID"]

# Ed25519 SPKI prefix (DER-encoded SubjectPublicKeyInfo)
ED25519_SPKI_PREFIX = bytes([0x30, 0x2A, 0x30, 0x05, 0x06, 0x03, 0x2B, 0x65, 0x70, 0x03, 0x21, 0x00])


def raw_ed25519_signer(data: bytes) -> bytes:
    response = kms.sign(
        KeyId=key_id,
        Message=data,
        MessageType="RAW",
        SigningAlgorithm="ED25519_SHA_512",
    )
    signature = response["Signature"]
    if signature is None:
        raise ValueError("No signature returned from KMS")
    return bytes(signature) if isinstance(signature, memoryview) else signature


pubkey_response = kms.get_public_key(KeyId=key_id)
spki_pubkey = bytes(pubkey_response["PublicKey"])

if not spki_pubkey[:12] == ED25519_SPKI_PREFIX:
    raise ValueError("Unexpected public key format")

ed25519_pubkey = spki_pubkey[12:]  # 32 bytes

algorand_account = generate_address_with_signers(ed25519_pubkey, raw_ed25519_signer)

algorand = AlgorandClient.default_localnet()

algorand.account.ensure_funded_from_environment(algorand_account.addr, AlgoAmount.from_algo(1))
algorand.set_signer_from_account(algorand_account)

algorand.send.payment(
    PaymentParams(
        sender=algorand_account.addr,
        receiver=algorand_account.addr,
        amount=AlgoAmount.from_micro_algo(0),
    )
)
```

## Sharing Secrets and Multisig

It's common for an application to have multiple developers that can deploy changes to mainnet. It may be tempting to share a secret for a single account (manually or through a secrets manager), but this is **not recommended**. Instead, it is recommended to setup a multisig account between all the developers. The multisig account can be a 1/N threshold, which would still allow a single developer to make changes. The benefit of a multisig is that secrets do not need to be shared and all actions are immutably auditable on-chain. Each developer should then follow the practices outlined above.

```python
from algokit_transact import MultisigAccount, MultisigMetadata, generate_address_with_signers
from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams

addr_with_signers = generate_address_with_signers(ed25519_pubkey, raw_ed25519_signer)

msig_metadata = MultisigMetadata(
    version=1,
    threshold=1,
    addrs=[
        other_signer_addr,  # Address of the other signer
        addr_with_signers.addr,
    ],
)

algorand = AlgorandClient.default_localnet()

# Create a multisig account that can be used to sign as a 1/N signer
msig_account = algorand.account.multisig(msig_metadata, [addr_with_signers])

# Send a transaction using the multisig account
algorand.send.payment(
    PaymentParams(
        sender=msig_account.addr,
        receiver=other_signer_addr,
        amount=AlgoAmount.from_micro_algo(0),
    )
)
```

## Key Rotation

Algorand has native support for key rotation through a feature called rekeying. Rekeying allows the blockchain address to stay the same while allowing for rotation of the underlying keypair. For example, a common pattern is to have an admin address that can deploy changes to a production contract. Rekeying allows the admin address to remain constant in the contract but allow the secrets used to authorize transactions to rotate. Rekeying can be done with any transaction type, but the simplest is to do a 0 ALGO payment to oneself with the `rekey_to` field set.

```python
from algokit_transact import generate_address_with_signers
from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams

original_addr_with_signers = generate_address_with_signers(original_pubkey, original_signer)

new_addr_with_signers = generate_address_with_signers(
    new_pubkey,
    new_signer,
    # NOTE: We are specifying sending_address so we can properly sign transactions
    # on behalf of the original address
    sending_address=original_addr_with_signers.addr,
)

algorand = AlgorandClient.default_localnet()

algorand.send.payment(
    PaymentParams(
        sender=original_addr_with_signers.addr,
        receiver=original_addr_with_signers.addr,
        amount=AlgoAmount.from_micro_algo(0),
        rekey_to=new_addr_with_signers.addr,
    )
)
```
