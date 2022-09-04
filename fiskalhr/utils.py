from decimal import Decimal
from typing import Union


def to_decimal2(value: Union[Decimal, int, str, float]) -> Decimal:
    """
    Cast value to Decimal with 2 decimal digits

    Args:
        value: value to convert to decimal

    Returns:
        `value` converted to Decimal with two decimal places
    """

    return Decimal(value).quantize(Decimal("1.00"))
