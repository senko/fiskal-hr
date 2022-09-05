from decimal import Decimal

from fiskalhr.utils import to_decimal2


def test_int_to_decimal():
    assert to_decimal2(42) == Decimal("42.00")


def test_string_to_decimal():
    assert to_decimal2("3.14") == Decimal("3.14")


def test_float_to_decimal():
    assert to_decimal2(3.1415) == Decimal("3.14")


def test_decimal_to_decimal():
    assert to_decimal2(Decimal("3.14")) == Decimal("3.14")


def test_decimal_rounding():
    assert to_decimal2(Decimal("3.141592")) == Decimal("3.14")


def test_decimal_ensures_two_decimal_places():
    assert to_decimal2(Decimal("1")) == Decimal("1.00")
