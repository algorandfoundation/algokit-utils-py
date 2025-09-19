# algokit_utils.models.state.BoxReference

#### *class* algokit_utils.models.state.BoxReference(app_id: int, name: bytes | str)

Bases: `algosdk.box_reference.BoxReference`

Represents a box reference with a foreign app index and the box name.

Args:
: app_index (int): index of the application in the foreign app array
  name (bytes): key for the box in bytes
