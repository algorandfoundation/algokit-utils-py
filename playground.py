from algokit_utils import get_localnet_default_account
from algokit_utils.account import TransactionSignerAccount
from algokit_utils.network_clients import get_algod_client, get_default_localnet_config

from src.algokit_utils.beta.composer import AlgoKitComposer

algod_client = get_algod_client(get_default_localnet_config("algod"))
legacy_account = get_localnet_default_account(algod_client)
signer = TransactionSignerAccount(address=legacy_account.address, signer=legacy_account.signer)

composer = AlgoKitComposer(algod_client, get_signer=lambda _: signer.signer)

note_test = AlgoKitComposer.arc2_note(dapp_name="a", format_type="u", data="abc")
assert note_test == b"a:uabc"
