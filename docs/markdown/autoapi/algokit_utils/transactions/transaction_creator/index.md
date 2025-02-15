# algokit_utils.transactions.transaction_creator

## Classes

| [`AlgorandClientTransactionCreator`](#algokit_utils.transactions.transaction_creator.AlgorandClientTransactionCreator)   | A creator for Algorand transactions.   |
|--------------------------------------------------------------------------------------------------------------------------|----------------------------------------|

## Module Contents

### *class* algokit_utils.transactions.transaction_creator.AlgorandClientTransactionCreator(new_group: collections.abc.Callable[[], [algokit_utils.transactions.transaction_composer.TransactionComposer](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.TransactionComposer)])

A creator for Algorand transactions.

Provides methods to create various types of Algorand transactions including payments,
asset operations, application calls and key registrations.

* **Parameters:**
  **new_group** – A lambda that starts a new TransactionComposer transaction group
* **Example:**
  ```pycon
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> creator.payment(PaymentParams(sender="sender", receiver="receiver", amount=AlgoAmount.from_algo(1)))
  ```

#### *property* payment *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.PaymentParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.PaymentParams)], algosdk.transaction.Transaction]*

Create a payment transaction to transfer Algo between accounts.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> creator.payment(PaymentParams(sender="sender", receiver="receiver", amount=AlgoAmount.from_algo(4)))
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.payment(PaymentParams(
          sender="SENDERADDRESS",
          receiver="RECEIVERADDRESS",
          amount=AlgoAmount.from_algo(4),
          close_remainder_to="CLOSEREMAINDERTOADDRESS",
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
      ))
  ```

#### *property* asset_create *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AssetCreateParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AssetCreateParams)], algosdk.transaction.Transaction]*

Create a create Algorand Standard Asset transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AssetCreateParams(sender="SENDER_ADDRESS", total=1000)
  >>> txn = creator.asset_create(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.asset_create(AssetCreateParams(
          sender="SENDER_ADDRESS",
          total=1000,
          asset_name="MyAsset",
          unit_name="MA",
          url="https://example.com/asset",
          decimals=0,
          default_frozen=False,
          manager="MANAGER_ADDRESS",
          reserve="RESERVE_ADDRESS",
          freeze="FREEZE_ADDRESS",
          clawback="CLAWBACK_ADDRESS",
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* asset_config *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AssetConfigParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AssetConfigParams)], algosdk.transaction.Transaction]*

Create an asset config transaction to reconfigure an existing Algorand Standard Asset.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AssetConfigParams(sender="SENDER_ADDRESS", asset_id=123456, manager="NEW_MANAGER_ADDRESS")
  >>> txn = creator.asset_config(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.asset_config(AssetConfigParams(
          sender="SENDER_ADDRESS",
          asset_id=123456,
          manager="NEW_MANAGER_ADDRESS",
          reserve="NEW_RESERVE_ADDRESS",
          freeze="NEW_FREEZE_ADDRESS",
          clawback="NEW_CLAWBACK_ADDRESS",
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* asset_freeze *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AssetFreezeParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AssetFreezeParams)], algosdk.transaction.Transaction]*

Create an Algorand Standard Asset freeze transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AssetFreezeParams(sender="SENDER_ADDRESS",
      asset_id=123456,
      account="ACCOUNT_TO_FREEZE",
      frozen=True)
  >>> txn = creator.asset_freeze(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.asset_freeze(AssetFreezeParams(
          sender="SENDER_ADDRESS",
          asset_id=123456,
          account="ACCOUNT_TO_FREEZE",
          frozen=True,
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* asset_destroy *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AssetDestroyParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AssetDestroyParams)], algosdk.transaction.Transaction]*

Create an Algorand Standard Asset destroy transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AssetDestroyParams(sender="SENDER_ADDRESS", asset_id=123456)
  >>> txn = creator.asset_destroy(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.asset_destroy(AssetDestroyParams(
          sender="SENDER_ADDRESS",
          asset_id=123456,
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* asset_transfer *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AssetTransferParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AssetTransferParams)], algosdk.transaction.Transaction]*

Create an Algorand Standard Asset transfer transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AssetTransferParams(sender="SENDER_ADDRESS",
      asset_id=123456,
      amount=10,
      receiver="RECEIVER_ADDRESS")
  >>> txn = creator.asset_transfer(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.asset_transfer(AssetTransferParams(
          sender="SENDER_ADDRESS",
          asset_id=123456,
          amount=10,
          receiver="RECEIVER_ADDRESS",
          clawback_target="CLAWBACK_TARGET_ADDRESS",
          close_asset_to="CLOSE_ASSET_TO_ADDRESS",
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* asset_opt_in *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AssetOptInParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AssetOptInParams)], algosdk.transaction.Transaction]*

Create an Algorand Standard Asset opt-in transaction.

* **Example:**
  ```pycon
  >>> # Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AssetOptInParams(sender="SENDER_ADDRESS", asset_id=123456)
  >>> txn = creator.asset_opt_in(params)
  ```
* **Example:**
  ```pycon
  >>> # Advanced example
  >>> creator.asset_opt_in(AssetOptInParams(
          sender="SENDER_ADDRESS",
          asset_id=123456,
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* asset_opt_out *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AssetOptOutParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AssetOptOutParams)], algosdk.transaction.Transaction]*

Create an asset opt-out transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AssetOptOutParams(sender="SENDER_ADDRESS", asset_id=123456, creator="CREATOR_ADDRESS")
  >>> txn = creator.asset_opt_out(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.asset_opt_out(AssetOptOutParams(
          sender="SENDER_ADDRESS",
          asset_id=123456,
          creator="CREATOR_ADDRESS",
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* app_create *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AppCreateParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppCreateParams)], algosdk.transaction.Transaction]*

Create an application create transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AppCreateParams(
  ...     sender="SENDER_ADDRESS",
  ...     approval_program="TEAL_APPROVAL_CODE",
  ...     clear_state_program="TEAL_CLEAR_CODE",
  ...     schema={
  ...         'global_ints': 1,
  ...         'global_byte_slices': 1,
  ...         'local_ints': 1,
  ...         'local_byte_slices': 1
  ...     }
  ... )
  >>> txn = creator.app_create(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.app_create(AppCreateParams(
          sender="SENDER_ADDRESS",
          approval_program="TEAL_APPROVAL_CODE",
          clear_state_program="TEAL_CLEAR_CODE",
          schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
          on_complete=OnComplete.NoOpOC,
          args=[b'arg1', b'arg2'],
          account_references=["ACCOUNT1"],
          app_references=[789],
          asset_references=[123],
          box_references=[],
          extra_program_pages=0,
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* app_update *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AppUpdateParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppUpdateParams)], algosdk.transaction.Transaction]*

Create an application update transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> txn = creator.app_update(AppUpdateParams(sender="SENDER_ADDRESS",
      app_id=789,
      approval_program="TEAL_NEW_APPROVAL_CODE",
      clear_state_program="TEAL_NEW_CLEAR_CODE",
      args=[b'new_arg1', b'new_arg2']))
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.app_update(AppUpdateParams(
          sender="SENDER_ADDRESS",
          app_id=789,
          approval_program="TEAL_NEW_APPROVAL_CODE",
          clear_state_program="TEAL_NEW_CLEAR_CODE",
          args=[b'new_arg1', b'new_arg2'],
          account_references=["ACCOUNT1"],
          app_references=[789],
          asset_references=[123],
          box_references=[],
          on_complete=OnComplete.UpdateApplicationOC,
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* app_delete *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AppDeleteParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppDeleteParams)], algosdk.transaction.Transaction]*

Create an application delete transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AppDeleteParams(sender="SENDER_ADDRESS", app_id=789, args=[b'delete_arg'])
  >>> txn = creator.app_delete(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.app_delete(AppDeleteParams(
          sender="SENDER_ADDRESS",
          app_id=789,
          args=[b'delete_arg'],
          account_references=["ACCOUNT1"],
          app_references=[789],
          asset_references=[123],
          box_references=[],
          on_complete=OnComplete.DeleteApplicationOC,
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* app_call *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AppCallParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppCallParams)], algosdk.transaction.Transaction]*

Create an application call transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AppCallParams(
  ...     sender="SENDER_ADDRESS",
  ...     on_complete=OnComplete.NoOpOC,
  ...     app_id=789,
  ...     approval_program="TEAL_APPROVAL_CODE",
  ...     clear_state_program="TEAL_CLEAR_CODE",
  ...     schema={
  ...         'global_ints': 1,
  ...         'global_byte_slices': 1,
  ...         'local_ints': 1,
  ...         'local_byte_slices': 1
  ...     },
  ...     args=[b'arg1', b'arg2'],
  ...     account_references=["ACCOUNT1"],
  ...     app_references=[789],
  ...     asset_references=[123],
  ...     extra_pages=0,
  ...     box_references=[]
  ... )
  >>> txn = creator.app_call(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.app_call(AppCallParams(
          sender="SENDER_ADDRESS",
          on_complete=OnComplete.NoOpOC,
          app_id=789,
          approval_program="TEAL_APPROVAL_CODE",
          clear_state_program="TEAL_CLEAR_CODE",
          schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
          args=[b'arg1', b'arg2'],
          account_references=["ACCOUNT1"],
          app_references=[789],
          asset_references=[123],
          extra_pages=0,
          box_references=[],
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* app_create_method_call *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppCreateMethodCallParams)], [algokit_utils.transactions.transaction_composer.BuiltTransactions](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.BuiltTransactions)]*

Create an application create call with ABI method call transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AppCreateMethodCallParams(sender="SENDER_ADDRESS", app_id=0, method=some_abi_method_object)
  >>> built_txns = creator.app_create_method_call(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.app_create_method_call(AppCreateMethodCallParams(
          sender="SENDER_ADDRESS",
          app_id=0,
          method=some_abi_method_object,
          args=[b'method_arg'],
          account_references=["ACCOUNT1"],
          app_references=[789],
          asset_references=[123],
          box_references=[],
          schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
          approval_program="TEAL_APPROVAL_CODE",
          clear_state_program="TEAL_CLEAR_CODE",
          on_complete=OnComplete.NoOpOC,
          extra_program_pages=0,
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* app_update_method_call *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppUpdateMethodCallParams)], [algokit_utils.transactions.transaction_composer.BuiltTransactions](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.BuiltTransactions)]*

Create an application update call with ABI method call transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AppUpdateMethodCallParams(sender="SENDER_ADDRESS", app_id=789, method=some_abi_method_object)
  >>> built_txns = creator.app_update_method_call(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.app_update_method_call(AppUpdateMethodCallParams(
          sender="SENDER_ADDRESS",
          app_id=789,
          method=some_abi_method_object,
          args=[b'method_arg'],
          account_references=["ACCOUNT1"],
          app_references=[789],
          asset_references=[123],
          box_references=[],
          schema={'global_ints': 1, 'global_byte_slices': 1, 'local_ints': 1, 'local_byte_slices': 1},
          approval_program="TEAL_NEW_APPROVAL_CODE",
          clear_state_program="TEAL_NEW_CLEAR_CODE",
          on_complete=OnComplete.UpdateApplicationOC,
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* app_delete_method_call *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppDeleteMethodCallParams)], [algokit_utils.transactions.transaction_composer.BuiltTransactions](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.BuiltTransactions)]*

Create an application delete call with ABI method call transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AppDeleteMethodCallParams(sender="SENDER_ADDRESS", app_id=789, method=some_abi_method_object)
  >>> built_txns = creator.app_delete_method_call(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.app_delete_method_call(AppDeleteMethodCallParams(
          sender="SENDER_ADDRESS",
          app_id=789,
          method=some_abi_method_object,
          args=[b'method_arg'],
          account_references=["ACCOUNT1"],
          app_references=[789],
          asset_references=[123],
          box_references=[],
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* app_call_method_call *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.AppCallMethodCallParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.AppCallMethodCallParams)], [algokit_utils.transactions.transaction_composer.BuiltTransactions](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.BuiltTransactions)]*

Create an application call with ABI method call transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = AppCallMethodCallParams(sender="SENDER_ADDRESS", app_id=789, method=some_abi_method_object)
  >>> built_txns = creator.app_call_method_call(params)
  ```
* **Example:**
  Advanced example
  >>> creator.app_call_method_call(AppCallMethodCallParams(
  > sender=”SENDER_ADDRESS”,
  > app_id=789,
  > method=some_abi_method_object,
  > args=[b’method_arg’],
  > account_references=[“ACCOUNT1”],
  > app_references=[789],
  > asset_references=[123],
  > box_references=[],
  > lease=”lease”,
  > note=b”note”,
  > rekey_to=”REKEYTOADDRESS”,
  > first_valid_round=1000,
  > validity_window=10,
  > extra_fee=AlgoAmount.from_micro_algo(1000),
  > static_fee=AlgoAmount.from_micro_algo(1000),
  > max_fee=AlgoAmount.from_micro_algo(3000)

  ))

#### *property* online_key_registration *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.OnlineKeyRegistrationParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.OnlineKeyRegistrationParams)], algosdk.transaction.Transaction]*

Create an online key registration transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> params = OnlineKeyRegistrationParams(
          sender="SENDER_ADDRESS",
          vote_key="VOTE_KEY",
          selection_key="SELECTION_KEY",
          vote_first=1000,
          vote_last=2000,
          vote_key_dilution=10,
          state_proof_key=b"state_proof_key_bytes"
  )
  >>> txn = creator.online_key_registration(params)
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.online_key_registration(OnlineKeyRegistrationParams(
          sender="SENDER_ADDRESS",
          vote_key="VOTE_KEY",
          selection_key="SELECTION_KEY",
          vote_first=1000,
          vote_last=2000,
          vote_key_dilution=10,
          state_proof_key=b"state_proof_key_bytes",
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```

#### *property* offline_key_registration *: collections.abc.Callable[[[algokit_utils.transactions.transaction_composer.OfflineKeyRegistrationParams](../transaction_composer/index.md#algokit_utils.transactions.transaction_composer.OfflineKeyRegistrationParams)], algosdk.transaction.Transaction]*

Create an offline key registration transaction.

* **Example:**
  ```pycon
  >>> #Basic example
  >>> creator = AlgorandClientTransactionCreator(lambda: TransactionComposer())
  >>> txn = creator.offline_key_registration(OfflineKeyRegistrationParams(sender="SENDER_ADDRESS",
      prevent_account_from_ever_participating_again=True))
  ```
* **Example:**
  ```pycon
  >>> #Advanced example
  >>> creator.offline_key_registration(OfflineKeyRegistrationParams(
          sender="SENDER_ADDRESS",
          prevent_account_from_ever_participating_again=True,
          lease="lease",
          note=b"note",
          rekey_to="REKEYTOADDRESS",
          first_valid_round=1000,
          validity_window=10,
          extra_fee=AlgoAmount.from_micro_algo(1000),
          static_fee=AlgoAmount.from_micro_algo(1000),
          max_fee=AlgoAmount.from_micro_algo(3000)
  ))
  ```
