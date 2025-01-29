# algokit_utils.models.state

## Attributes

| [`TealTemplateParams`](#algokit_utils.models.state.TealTemplateParams)   |    |
|--------------------------------------------------------------------------|----|
| [`BoxIdentifier`](#algokit_utils.models.state.BoxIdentifier)             |    |

## Classes

| [`BoxName`](#algokit_utils.models.state.BoxName)           |                                                                       |
|------------------------------------------------------------|-----------------------------------------------------------------------|
| [`BoxValue`](#algokit_utils.models.state.BoxValue)         |                                                                       |
| [`DataTypeFlag`](#algokit_utils.models.state.DataTypeFlag) | Enum where members are also (and must be) ints                        |
| [`BoxReference`](#algokit_utils.models.state.BoxReference) | Represents a box reference with a foreign app index and the box name. |

## Module Contents

### *class* algokit_utils.models.state.BoxName

#### name *: str*

#### name_raw *: bytes*

#### name_base64 *: str*

### *class* algokit_utils.models.state.BoxValue

#### name *: [BoxName](#algokit_utils.models.state.BoxName)*

#### value *: bytes*

### *class* algokit_utils.models.state.DataTypeFlag

Bases: `enum.IntEnum`

Enum where members are also (and must be) ints

#### BYTES *= 1*

#### UINT *= 2*

### algokit_utils.models.state.TealTemplateParams *: TypeAlias* *= Mapping[str, str | int | bytes] | dict[str, str | int | bytes]*

### algokit_utils.models.state.BoxIdentifier *: TypeAlias* *= str | bytes | AccountTransactionSigner*

### *class* algokit_utils.models.state.BoxReference(app_id: int, name: bytes | str)

Bases: `algosdk.box_reference.BoxReference`

Represents a box reference with a foreign app index and the box name.

Args:
: app_index (int): index of the application in the foreign app array
  name (bytes): key for the box in bytes
