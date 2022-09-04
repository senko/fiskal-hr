from decimal import Decimal

from .utils import to_decimal2


class TaxItem:
    def __init__(self, base: Decimal, rate: Decimal, amount: Decimal):
        self.base = to_decimal2(base)
        self.rate = to_decimal2(rate)
        self.amount = to_decimal2(amount)

        calculated = (self.base * self.rate / Decimal("100")).quantize(Decimal("1.00"))
        if calculated != self.amount:
            raise ValueError(
                f"Calculated tax amount {calculated} differs from provided {self.amount}"
            )

    def __str__(self):
        return f"{self.rate}%"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TaxItem)
            and self.base == other.base
            and self.rate == other.rate
            and self.amount == other.amount
        )


class NamedTaxItem(TaxItem):
    def __init__(self, name: str, base: Decimal, rate: Decimal, amount: Decimal):
        super().__init__(base, rate, amount)
        self.name = name

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, NamedTaxItem)
            and super().__eq__(other)
            and self.name == other.name
        )


class Fee:
    def __init__(self, name: str, amount: Decimal):
        self.name = name
        self.amount = to_decimal2(amount)

    def __str__(self):
        return self.name

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Fee)
            and self.name == other.name
            and self.amount == other.amount
        )
