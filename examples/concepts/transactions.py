"""Demonstrates constructing, configuring, signing and sending transactions.

This maps to the Concepts -> Transactions docs page. Each marked region is
rendered into the page via RemoteCode, so the code shown in the docs is real,
executed code.

Prerequisites:
- A running LocalNet (``algokit localnet start``).
- Run with ``uv run --frozen python -m examples.concepts.transactions``.
"""

from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    MultisigMetadata,
    OfflineKeyRegistrationParams,
    OnlineKeyRegistrationParams,
    PaymentParams,
    SigningAccount,
    TransactionComposer,
)
from examples._helpers import setup_localnet_environment


def _new_funded_account(algorand: AlgorandClient, funder: SigningAccount, amount: AlgoAmount) -> SigningAccount:
    """Create a fresh random account (signer auto-registered) and fund it from ``funder``."""
    account = algorand.account.random()
    algorand.send.payment(PaymentParams(sender=funder.address, receiver=account.address, amount=amount))
    return account


def main() -> None:
    algorand, account_a, account_b = setup_localnet_environment(initial_funds=AlgoAmount.from_algo(30))

    balance_before = algorand.account.get_information(account_b.address).amount

    # example: SEND_PAYMENT
    result = algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
        )
    )
    print(f"Payment sent in transaction {result.tx_id}")
    # example: SEND_PAYMENT

    balance_after = algorand.account.get_information(account_b.address).amount
    assert balance_after.micro_algo == balance_before.micro_algo + AlgoAmount.from_algo(1).micro_algo

    # Closing an account empties it, so use a throwaway account rather than account_a.
    closing_account = _new_funded_account(algorand, account_a, AlgoAmount.from_algo(1))

    # example: CLOSE_ACCOUNT
    # close_remainder_to sends the whole remaining balance and removes the
    # sender account from the ledger. amount is what to send on top of the close.
    algorand.send.payment(
        PaymentParams(
            sender=closing_account.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(0),
            close_remainder_to=account_b.address,
        )
    )
    # example: CLOSE_ACCOUNT

    assert algorand.account.get_information(closing_account.address).amount.micro_algo == 0

    # Key registration is a node-participation action, so use a dedicated account.
    participant = _new_funded_account(algorand, account_a, AlgoAmount.from_algo(1))
    params = algorand.get_suggested_params()

    # example: KEY_REGISTRATION_ONLINE
    # Bring an account online for consensus participation. The vote and
    # selection keys come from participation keys generated on a node.
    algorand.send.online_key_registration(
        OnlineKeyRegistrationParams(
            sender=participant.address,
            vote_key="G/lqTV6MKspW6J8wH2d8ZliZ5XZVZsruqSBJMwLwlmo=",
            selection_key="LrpLhvzr+QpN/bivh6IPpOaKGbGzTTB5lJtVfixmmgk=",
            state_proof_key=b"RpUpNWfZMjZ1zOOjv3MF2tjO714jsBt0GKnNsw0ihJ4HSZwci+d9zvUi3i67LwFUJgjQ5Dz4zZgHgGduElnmSA==",
            vote_first=params.first,
            vote_last=params.first + 10_000_000,
            vote_key_dilution=100,
        )
    )
    # example: KEY_REGISTRATION_ONLINE

    # example: KEY_REGISTRATION_OFFLINE
    # Take an account offline so it no longer participates in consensus.
    algorand.send.offline_key_registration(
        OfflineKeyRegistrationParams(
            sender=participant.address,
            prevent_account_from_ever_participating_again=False,
        )
    )
    # example: KEY_REGISTRATION_OFFLINE

    # example: STATIC_FEE
    # static_fee overrides the calculated fee with an exact amount.
    algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            static_fee=AlgoAmount.from_micro_algo(1000),
            note=b"fixed-fee payment",
        )
    )
    # example: STATIC_FEE

    # example: EXTRA_FEE
    # extra_fee adds to the fee the client already calculated instead of
    # replacing it, so this payment pays the minimum fee plus 1000 microAlgo.
    algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            extra_fee=AlgoAmount.from_micro_algo(1000),
            note=b"extra-fee payment",
        )
    )
    # example: EXTRA_FEE

    # example: MAX_FEE
    # max_fee caps the fee the client will accept; sending raises if the
    # calculated fee would exceed it, guarding against fee spikes.
    algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            max_fee=AlgoAmount.from_micro_algo(2000),
            note=b"capped-fee payment",
        )
    )
    # example: MAX_FEE

    # example: FEE_POOLING
    # In a group the network only requires the total fee to cover every
    # transaction. Here the second payment pays both fees and the first pays
    # none, so a sponsor can cover a fee-less transaction's cost.
    algorand.new_group().add_payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            static_fee=AlgoAmount.from_micro_algo(0),
        )
    ).add_payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            static_fee=AlgoAmount.from_micro_algo(2000),
        )
    ).send()
    # example: FEE_POOLING

    # example: LEASE
    # A lease locks the (sender, lease) pair until the transaction's last-valid
    # round, so no second transaction with the same pair can also confirm.
    algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            lease=b"payroll-2024-01",
        )
    )
    # example: LEASE

    # example: MULTISIG
    # A multisig account is authorized by a threshold of its member accounts.
    # Create it from the members; sending from it is then signed by the members
    # registered against it (here a 2-of-2), with no explicit signer needed.
    multisig = algorand.account.multisig(
        metadata=MultisigMetadata(
            version=1,
            threshold=2,
            addresses=[account_a.address, account_b.address],
        ),
        signing_accounts=[account_a, account_b],
    )
    algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=multisig.address,
            amount=AlgoAmount.from_algo(1),
        )
    )
    algorand.send.payment(
        PaymentParams(
            sender=multisig.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_micro_algo(100_000),
        )
    )
    # example: MULTISIG

    # example: LOGICSIG
    # A logic signature is a compiled program that authorizes transactions. This
    # one approves unconditionally (int 1); a real program encodes spending rules.
    program = algorand.app.compile_teal("#pragma version 10\nint 1").compiled_base64_to_bytes
    logic_sig = algorand.account.logicsig(program)

    # The program's hash is a contract (escrow) account. Fund it, then spend from
    # it — the logic signature authorizes the payment, so no private key signs.
    algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=logic_sig.address,
            amount=AlgoAmount.from_algo(1),
        )
    )
    algorand.send.payment(
        PaymentParams(
            sender=logic_sig.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_micro_algo(100_000),
        )
    )
    # example: LOGICSIG

    # example: ATOMIC_GROUP
    # Transactions added to a group either all confirm or all fail together.
    group_result = (
        algorand.new_group()
        .add_payment(
            PaymentParams(
                sender=account_a.address,
                receiver=account_b.address,
                amount=AlgoAmount.from_algo(1),
                note=b"group payment 1",
            )
        )
        .add_payment(
            PaymentParams(
                sender=account_b.address,
                receiver=account_a.address,
                amount=AlgoAmount.from_algo(2),
                note=b"group payment 2",
            )
        )
        .send()
    )
    print(f"Group {group_result.group_id} sent {len(group_result.tx_ids)} transactions")
    # example: ATOMIC_GROUP

    assert len(group_result.tx_ids) == 2

    # example: SIMULATE
    # Simulate runs the group against the current ledger without submitting it.
    # skip_signatures lets you preview execution without signing.
    simulation = (
        algorand.new_group()
        .add_payment(
            PaymentParams(
                sender=account_a.address,
                receiver=account_b.address,
                amount=AlgoAmount.from_algo(1),
                note=b"simulated payment",
            )
        )
        .simulate(skip_signatures=True)
    )
    print(f"Simulated {len(simulation.transactions)} transaction(s) before sending")
    # example: SIMULATE

    assert len(simulation.transactions) == 1

    # example: ADD_TRANSACTION
    # A transaction built elsewhere — here via create_transaction, but any algosdk
    # transaction works — can be dropped into a group alongside params-built ones.
    prebuilt_txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            note=b"prebuilt txn",
        )
    )
    algorand.new_group().add_transaction(prebuilt_txn).add_payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            note=b"group with prebuilt",
        )
    ).send()
    # example: ADD_TRANSACTION

    # example: BUILD_UNSIGNED
    # create_transaction builds the transaction without signing or sending it, so
    # you can hand it to a wallet or sign it yourself.
    unsigned_txn = algorand.create_transaction.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            note=b"manually signed",
        )
    )
    # Sign with the sender's key and submit through the underlying algod client.
    signed_txn = unsigned_txn.sign(account_a.private_key)
    tx_id = algorand.client.algod.send_transaction(signed_txn)
    # example: BUILD_UNSIGNED

    assert tx_id

    # example: ARC2_NOTE
    # ARC-2 is a convention for structured transaction notes. arc2_note encodes a
    # note as "<dapp_name>:<format><data>"; pass the resulting bytes as the note.
    note = TransactionComposer.arc2_note({"dapp_name": "my-dapp", "format": "j", "data": {"amount": 1}})
    algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            note=note,
        )
    )
    # example: ARC2_NOTE

    # example: SEND_PARAMS
    # send_params tunes how a transaction is sent, not what it contains. Pass it to
    # any send call — here, wait up to 10 rounds for confirmation and suppress logs.
    algorand.send.payment(
        PaymentParams(
            sender=account_a.address,
            receiver=account_b.address,
            amount=AlgoAmount.from_algo(1),
            note=b"custom send params",
        ),
        send_params={"max_rounds_to_wait": 10, "suppress_log": True},
    )
    # example: SEND_PARAMS

    # example: ERROR_TRANSFORMER
    # An error transformer rewrites a failure the composer catches into a clearer,
    # application-specific message. Register it on the client (or on one group) and
    # it runs whenever a send or simulate in that group raises.
    def clarify_overspend(error: Exception) -> Exception:
        if "overspend" in str(error).lower():
            return Exception("Payment exceeds the sender's available balance")
        return error  # return the original error unchanged when it does not apply

    algorand.register_error_transformer(clarify_overspend)
    try:
        algorand.new_group().add_payment(
            PaymentParams(
                sender=account_a.address,
                receiver=account_b.address,
                amount=AlgoAmount.from_algo(1_000_000_000),  # far more than the balance
            )
        ).send()
    except Exception as exc:
        print(f"Transformed error: {exc}")
    algorand.unregister_error_transformer(clarify_overspend)
    # example: ERROR_TRANSFORMER


if __name__ == "__main__":
    main()
