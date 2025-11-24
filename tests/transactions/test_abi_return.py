import algokit_abi
from algokit_utils.applications.abi import ABIResult, ABIReturn, ABIValue
from algokit_utils.applications.app_spec import arc56


def get_abi_result(type_str: str, value: ABIValue) -> ABIReturn:
    """Helper function to simulate ABI method return value"""
    abi_type = algokit_abi.ABIType.from_string(type_str)
    encoded = abi_type.encode(value)
    decoded = abi_type.decode(encoded)
    result = ABIResult(
        method=arc56.Method(
            name="",
            args=(),
            returns=arc56.Returns(type=abi_type),
            actions=arc56.Actions(call=(), create=()),
        ),
        raw_value=encoded,
        return_value=decoded,
        tx_id="",
        tx_info=None,
        decode_error=None,
    )

    return ABIReturn(result)


class TestABIReturn:
    def test_uint32(self) -> None:
        assert get_abi_result("uint32", 0).value == 0
        assert get_abi_result("uint32", 0).value == 0
        assert get_abi_result("uint32", 1).value == 1
        assert get_abi_result("uint32", 1).value == 1
        assert get_abi_result("uint32", 2**32 - 1).value == 2**32 - 1
        assert get_abi_result("uint32", 2**32 - 1).value == 2**32 - 1

    def test_uint64(self) -> None:
        assert get_abi_result("uint64", 0).value == 0
        assert get_abi_result("uint64", 1).value == 1
        assert get_abi_result("uint64", 2**32 - 1).value == 2**32 - 1
        assert get_abi_result("uint64", 2**64 - 1).value == 2**64 - 1

    def test_uint32_array(self) -> None:
        assert get_abi_result("uint32[]", [0]).value == [0]
        assert get_abi_result("uint32[]", [0]).value == [0]
        assert get_abi_result("uint32[]", [1]).value == [1]
        assert get_abi_result("uint32[]", [1]).value == [1]
        assert get_abi_result("uint32[]", [1, 2, 3]).value == [1, 2, 3]
        assert get_abi_result("uint32[]", [1, 2, 3]).value == [1, 2, 3]
        assert get_abi_result("uint32[]", [2**32 - 1]).value == [2**32 - 1]
        assert get_abi_result("uint32[]", [2**32 - 1, 1]).value == [2**32 - 1, 1]

    def test_uint32_fixed_array(self) -> None:
        assert get_abi_result("uint32[1]", [0]).value == [0]
        assert get_abi_result("uint32[1]", [0]).value == [0]
        assert get_abi_result("uint32[1]", [1]).value == [1]
        assert get_abi_result("uint32[1]", [1]).value == [1]
        assert get_abi_result("uint32[3]", [1, 2, 3]).value == [1, 2, 3]
        assert get_abi_result("uint32[3]", [1, 2, 3]).value == [1, 2, 3]
        assert get_abi_result("uint32[1]", [2**32 - 1]).value == [2**32 - 1]
        assert get_abi_result("uint32[2]", [2**32 - 1, 1]).value == [2**32 - 1, 1]

    def test_uint64_array(self) -> None:
        assert get_abi_result("uint64[]", [0]).value == [0]
        assert get_abi_result("uint64[]", [0]).value == [0]
        assert get_abi_result("uint64[]", [1]).value == [1]
        assert get_abi_result("uint64[]", [1]).value == [1]
        assert get_abi_result("uint64[]", [1, 2, 3]).value == [1, 2, 3]
        assert get_abi_result("uint64[]", [1, 2, 3]).value == [1, 2, 3]
        assert get_abi_result("uint64[]", [2**32 - 1]).value == [2**32 - 1]
        assert get_abi_result("uint64[]", [2**64 - 1, 1]).value == [2**64 - 1, 1]

    def test_uint64_fixed_array(self) -> None:
        assert get_abi_result("uint64[1]", [0]).value == [0]
        assert get_abi_result("uint64[1]", [0]).value == [0]
        assert get_abi_result("uint64[1]", [1]).value == [1]
        assert get_abi_result("uint64[1]", [1]).value == [1]
        assert get_abi_result("uint64[3]", [1, 2, 3]).value == [1, 2, 3]
        assert get_abi_result("uint64[3]", [1, 2, 3]).value == [1, 2, 3]
        assert get_abi_result("uint64[1]", [2**32 - 1]).value == [2**32 - 1]
        assert get_abi_result("uint64[2]", [2**64 - 1, 1]).value == [2**64 - 1, 1]

    def test_tuple(self) -> None:
        type_str = "(uint32,uint64,(uint32,uint64),uint32[],uint64[])"
        assert get_abi_result(type_str, [0, 0, [0, 0], [0], [0]]).value == (
            0,
            0,
            (0, 0),
            [0],
            [0],
        )
        assert get_abi_result(type_str, [1, 1, [1, 1], [1], [1]]).value == (
            1,
            1,
            (1, 1),
            [1],
            [1],
        )
        assert get_abi_result(
            type_str,
            [2**32 - 1, 2**64 - 1, [2**32 - 1, 2**64 - 1], [1, 2, 3], [1, 2, 3]],
        ).value == (
            2**32 - 1,
            2**64 - 1,
            (2**32 - 1, 2**64 - 1),
            [1, 2, 3],
            [1, 2, 3],
        )
