ABIPrimitiveValue = bool | int | str | bytes | bytearray

# NOTE: This is present in js-algorand-sdk, but sadly not in untyped py-algorand-sdk
ABIValue = ABIPrimitiveValue | list["ABIValue"] | dict[str, "ABIValue"]
