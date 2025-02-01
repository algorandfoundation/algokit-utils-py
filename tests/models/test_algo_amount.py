from decimal import Decimal

import pytest

from algokit_utils.models.amount import ALGORAND_MIN_TX_FEE, AlgoAmount, algo, micro_algo, transaction_fees


def test_initialization() -> None:
    # Test valid initialization formats
    assert AlgoAmount({"microAlgos": 1_000_000}).micro_algos == 1_000_000
    assert AlgoAmount({"microAlgo": 500_000}).micro_algos == 500_000
    assert AlgoAmount({"algos": 1}).micro_algos == 1_000_000
    assert AlgoAmount({"algo": Decimal("0.5")}).micro_algos == 500_000

    # Test decimal precision
    assert AlgoAmount({"algos": Decimal("0.000001")}).micro_algos == 1
    assert AlgoAmount({"algo": Decimal("123.456789")}).micro_algos == 123_456_789

    # Test invalid initialization
    with pytest.raises(ValueError, match="Invalid amount provided"):
        AlgoAmount({"invalid": 100})


def test_from_methods() -> None:
    assert AlgoAmount.from_micro_algos(500_000).micro_algos == 500_000
    assert AlgoAmount.from_micro_algo(250_000).micro_algos == 250_000
    assert AlgoAmount.from_algos(2).micro_algos == 2_000_000
    assert AlgoAmount.from_algo(Decimal("0.75")).micro_algos == 750_000


def test_properties() -> None:
    amount = AlgoAmount.from_micro_algos(1_234_567)
    assert amount.micro_algos == 1_234_567
    assert amount.micro_algo == 1_234_567
    assert amount.algos == Decimal("1.234567")
    assert amount.algo == Decimal("1.234567")


def test_arithmetic_operations() -> None:
    a = AlgoAmount.from_algos(5)
    b = AlgoAmount.from_algos(3)

    # Addition
    assert (a + b).micro_algos == 8_000_000
    a += b
    assert a.micro_algos == 8_000_000

    # Subtraction
    assert (a - b).micro_algos == 5_000_000
    a -= b
    assert a.micro_algos == 5_000_000

    # Right operations
    assert (AlgoAmount.from_micro_algo(1000) + a).micro_algos == 5_001_000
    assert (AlgoAmount.from_algos(10) - a).micro_algos == 5_000_000


def test_comparison_operators() -> None:
    base = AlgoAmount.from_algos(5)
    same = AlgoAmount.from_algos(5)
    larger = AlgoAmount.from_algos(10)

    assert base == same
    assert base != larger
    assert base < larger
    assert larger > base
    assert base <= same
    assert larger >= base

    # Test int comparison
    assert base == 5_000_000
    assert base < 6_000_000
    assert base > 4_000_000


def test_edge_cases() -> None:
    # Zero value
    zero = AlgoAmount.from_micro_algos(0)
    assert zero.micro_algos == 0
    assert zero.algos == 0

    # Very large values
    large = AlgoAmount.from_algos(Decimal("1e9"))
    assert large.micro_algos == 1e9 * 1e6

    # Decimal precision limits
    precise = AlgoAmount({"algos": Decimal("0.123456789")})
    assert precise.micro_algos == 123_456


def test_string_representation() -> None:
    assert str(AlgoAmount.from_micro_algos(1_000_000)) == "1,000,000 µALGO"
    assert str(AlgoAmount.from_algos(Decimal("2.5"))) == "2,500,000 µALGO"


def test_type_safety() -> None:
    with pytest.raises(TypeError, match="Unsupported operand type"):
        # int is not AlgoAmount
        AlgoAmount.from_algos(5) + 1000  # type: ignore  # noqa: PGH003

    with pytest.raises(TypeError, match="Unsupported operand type"):
        AlgoAmount.from_algos(5) - "invalid"  # type: ignore  # noqa: PGH003


def test_helper_functions() -> None:
    assert algo(1).micro_algos == 1_000_000
    assert micro_algo(1_000_000).micro_algos == 1_000_000
    assert ALGORAND_MIN_TX_FEE.micro_algos == 1_000
    assert transaction_fees(1).micro_algos == 1_000
