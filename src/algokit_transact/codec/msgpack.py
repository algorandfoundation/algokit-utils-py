from msgpack import packb, unpackb


def encode_msgpack(value: object) -> bytes:
    """Encode a Python value into canonical msgpack bytes."""
    return packb(value, use_bin_type=True, strict_types=True)


def decode_msgpack(data: bytes) -> object:
    """Decode msgpack bytes into a Python structure."""
    return unpackb(data, raw=False, strict_map_key=False)
