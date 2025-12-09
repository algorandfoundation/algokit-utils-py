import dataclasses
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import algokit_algosdk as algosdk
from algokit_transact import encode_signed_transaction, encode_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction as AlgokitTransaction
from algokit_transact.signer import (
    AddressWithSigners,
    DelegatedLsigSigner,
    ProgramDataSigner,
    TransactionSigner,
)
from algokit_transact.signing.multisig import (
    address_from_multisig_signature,
    apply_multisig_subsignature,
    new_multisig_signature,
)
from algokit_transact.signing.types import MultisigSignature

if TYPE_CHECKING:
    from collections.abc import Callable

    SanityCheckProgram = Callable[[bytes], None]


def _get_sanity_check_program() -> "SanityCheckProgram":
    """Get the sanity_check_program function from algokit_transact."""
    # Import at runtime to avoid circular imports and type checking issues
    from algokit_transact.signing.validation import (  # pyright: ignore[reportMissingImports]
        sanity_check_program,
    )

    return sanity_check_program


__all__ = [
    "DISPENSER_ACCOUNT_NAME",
    "AddressWithSigners",
    "LogicSigAccount",
    "MultisigAccount",
    "MultisigMetadata",
]


DISPENSER_ACCOUNT_NAME = "DISPENSER"


@dataclasses.dataclass(kw_only=True)
class MultisigMetadata:
    """Metadata for a multisig account."""

    version: int
    threshold: int
    addresses: list[str]


@dataclasses.dataclass(kw_only=True)
class MultisigAccount:
    """Account wrapper for multisig signing. Supports secretless signing."""

    _params: MultisigMetadata
    _sub_signers: Sequence[AddressWithSigners]
    _addr: str
    _signer: TransactionSigner
    _multisig_signature: MultisigSignature

    def __init__(
        self,
        multisig_params: MultisigMetadata,
        sub_signers: Sequence[AddressWithSigners],
    ) -> None:
        self._params = multisig_params
        self._sub_signers = sub_signers
        self._multisig_signature = new_multisig_signature(
            multisig_params.version,
            multisig_params.threshold,
            multisig_params.addresses,
        )
        self._addr = address_from_multisig_signature(self._multisig_signature)
        self._signer = self._create_multisig_signer()

    def _get_account_address(self, account: AddressWithSigners) -> str:
        """Get address from account, handling both AddressWithSigners and AddressWithSigners."""
        # Both AddressWithSigners and AddressWithSigners now use 'addr'
        return account.addr

    def _create_multisig_signer(self) -> TransactionSigner:
        # Use Callable type to accommodate both BytesSigner protocol and type alias
        address_to_signer: dict[str, Callable[[bytes], bytes]] = {
            self._get_account_address(account): account.bytes_signer for account in self._sub_signers
        }
        msig_address = self._addr
        base_multisig = self._multisig_signature

        def signer(txn_group: Sequence[AlgokitTransaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
            blobs: list[bytes] = []
            for index in indexes_to_sign:
                txn = txn_group[index]
                payload = encode_transaction(txn)

                multisig_sig = base_multisig
                for subsig in base_multisig.subsignatures:
                    if subsig.address in address_to_signer:
                        signature = address_to_signer[subsig.address](payload)
                        multisig_sig = apply_multisig_subsignature(multisig_sig, subsig.address, signature)

                signed = SignedTransaction(
                    transaction=txn,
                    signature=None,
                    multi_signature=multisig_sig,
                    logic_signature=None,
                    auth_address=msig_address if txn.sender != msig_address else None,
                )
                blobs.append(encode_signed_transaction(signed))
            return blobs

        return signer

    @property
    def params(self) -> MultisigMetadata:
        """The multisig account parameters."""
        return self._params

    @property
    def sub_signers(self) -> Sequence[AddressWithSigners]:
        """The list of signing accounts."""
        return self._sub_signers

    @property
    def address(self) -> str:
        """The multisig account address."""
        return self._addr

    @property
    def addr(self) -> str:
        """Alias for address property (matching TypeScript's get addr())."""
        return self.address

    @property
    def signer(self) -> TransactionSigner:
        """Transaction signer callable."""
        return self._signer


@dataclasses.dataclass(kw_only=True)
class LogicSigAccount:
    """Account wrapper for LogicSig signing. Supports delegation including secretless signing."""

    _program: bytes
    _args: list[bytes] | None
    _signature: bytes | None
    _multisig_signature: MultisigSignature | None
    _delegated_address: str | None
    _signer: TransactionSigner | None

    def __init__(self, program: bytes, args: list[bytes] | None = None) -> None:
        _get_sanity_check_program()(program)
        self._program = program
        self._args = args
        self._signature = None
        self._multisig_signature = None
        self._delegated_address = None
        self._signer = None

    @property
    def program(self) -> bytes:
        """The LogicSig program bytes."""
        return self._program

    @property
    def args(self) -> list[bytes] | None:
        """The arguments to pass to the LogicSig program."""
        return self._args

    @property
    def is_delegated(self) -> bool:
        """Whether this LogicSig is delegated to an account."""
        return self._signature is not None or self._multisig_signature is not None

    @property
    def address(self) -> str:
        """The LogicSig account address (delegated address or escrow address)."""
        if self._delegated_address is not None:
            return self._delegated_address

        from algokit_common import sha512_256
        from algokit_common.constants import PROGRAM_DOMAIN_SEPARATOR

        program_hash = sha512_256(PROGRAM_DOMAIN_SEPARATOR.encode() + self._program)
        address = algosdk.encoding.encode_address(program_hash)
        assert isinstance(address, str)
        return address

    @property
    def addr(self) -> str:
        """Alias for address property (matching TypeScript's get addr())."""
        return self.address

    @property
    def signer(self) -> TransactionSigner:
        """Transaction signer callable."""
        if self._signer is None:
            self._signer = self._create_logic_sig_signer()
        return self._signer

    def _create_logic_sig_signer(self) -> TransactionSigner:
        from algokit_transact.signing.logic_signature import LogicSignature

        program = self._program
        args = list(self._args) if self._args else None
        signature = self._signature
        multisig_sig = self._multisig_signature
        lsig_address = self.address

        def signer(txn_group: Sequence[AlgokitTransaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
            blobs: list[bytes] = []
            for index in indexes_to_sign:
                txn = txn_group[index]
                logic_sig = LogicSignature(
                    logic=program,
                    args=args,
                    signature=signature,
                    multi_signature=multisig_sig,
                )
                auth_addr = lsig_address if txn.sender != lsig_address else None

                signed = SignedTransaction(
                    transaction=txn,
                    signature=None,
                    multi_signature=None,
                    logic_signature=logic_sig,
                    auth_address=auth_addr,
                )
                blobs.append(encode_signed_transaction(signed))
            return blobs

        return signer

    def bytes_to_sign_for_delegation(self, msig: "MultisigAccount | None" = None) -> bytes:
        """Returns bytes to sign for delegation.

        Args:
            msig: Optional multisig account for multisig delegation.

        Returns:
            The bytes that need to be signed for delegation.
        """
        from algokit_common.constants import MULTISIG_PROGRAM_DOMAIN_SEPARATOR, PROGRAM_DOMAIN_SEPARATOR

        if msig is not None:
            msig_public_key = algosdk.encoding.decode_address(msig.address)
            assert isinstance(msig_public_key, bytes)
            return MULTISIG_PROGRAM_DOMAIN_SEPARATOR.encode() + msig_public_key + self._program
        return PROGRAM_DOMAIN_SEPARATOR.encode() + self._program

    def program_data_to_sign(self, data: bytes) -> bytes:
        """Returns bytes to sign for program data.

        Args:
            data: The data to sign.

        Returns:
            The bytes that need to be signed (ProgData + program_address + data).
        """
        from algokit_common.constants import LOGIC_DATA_DOMAIN_SEPARATOR

        program_address = algosdk.encoding.decode_address(self.address)
        assert isinstance(program_address, bytes)
        return LOGIC_DATA_DOMAIN_SEPARATOR.encode() + program_address + data

    def sign_program_data(self, data: bytes, signer: ProgramDataSigner) -> bytes:
        """Signs program data with given signer.

        Args:
            data: The data to sign.
            signer: The program data signer to use.

        Returns:
            The signature bytes.
        """
        program_address = algosdk.encoding.decode_address(self.address)
        assert isinstance(program_address, bytes)
        return signer(data, program_address)

    def delegate(self, signer: DelegatedLsigSigner, delegating_address: str | None = None) -> "LogicSigAccount":
        """Delegate this LogicSig to a single account. Returns self for chaining.

        Args:
            signer: The DelegatedLsigSigner callback to sign the program.
            delegating_address: Optional address of the delegating account.
                If not provided, the address must be set separately or
                the LogicSig will use the escrow address.

        Returns:
            Self for method chaining.
        """
        self._signature = signer(self._program, None)
        self._delegated_address = delegating_address
        self._multisig_signature = None
        self._signer = None
        return self

    def _get_lsig_account_address(self, account: AddressWithSigners) -> str:
        """Get address from account, handling both AddressWithSigners and AddressWithSigners."""
        # Both AddressWithSigners and AddressWithSigners now use 'addr'
        return account.addr

    def delegate_multisig(
        self,
        multisig_params: MultisigMetadata,
        signing_accounts: Sequence[AddressWithSigners],
    ) -> "LogicSigAccount":
        """Delegate this LogicSig to a multisig account. Returns self for chaining."""
        msig = new_multisig_signature(
            multisig_params.version,
            multisig_params.threshold,
            multisig_params.addresses,
        )

        msig_address = address_from_multisig_signature(msig)
        msig_public_key = algosdk.encoding.decode_address(msig_address)
        assert isinstance(msig_public_key, bytes)

        # Use Callable type to accommodate both DelegatedLsigSigner protocol and type alias
        address_to_signer: dict[str, Callable[[bytes, bytes | None], bytes]] = {
            self._get_lsig_account_address(account): account.delegated_lsig_signer for account in signing_accounts
        }

        for subsig in msig.subsignatures:
            if subsig.address in address_to_signer:
                signature = address_to_signer[subsig.address](self._program, msig_public_key)
                msig = apply_multisig_subsignature(msig, subsig.address, signature)

        self._multisig_signature = msig
        self._delegated_address = address_from_multisig_signature(msig)
        self._signature = None
        self._signer = None
        return self
