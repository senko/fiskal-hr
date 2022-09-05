from decimal import Decimal

import pytest

from fiskalhr.item import Fee, NamedTaxItem, TaxItem


def test_tax_item():
    item = TaxItem(100, 2.5, "2.5")

    assert item.base == Decimal("100.00")
    assert item.rate == Decimal("2.50")
    assert item.amount == Decimal("2.50")
    assert str(item) == "2.50%"


def test_tax_amount_verification():
    with pytest.raises(ValueError):
        TaxItem(100, 20, 30)


def test_tax_item_equality():
    item1 = TaxItem(100, 2.5, "2.5")
    item2 = TaxItem("100", "2.50", 2.5)

    assert item1 == item2


def test_tax_item_inequality():
    item1 = TaxItem(100, 5, 5)
    item2 = TaxItem(100, 4, 4)

    assert item1 != item2


def test_named_tax_item():
    item = NamedTaxItem("PDV", 100, 25, 25)

    assert item.name == "PDV"
    assert item.base == Decimal("100.00")
    assert item.rate == Decimal("25.00")
    assert item.amount == Decimal("25.00")

    assert str(item) == "PDV (25.00%)"


def test_named_tax_item_equality():
    item1 = NamedTaxItem("PDV", 100, 25, 25)
    item2 = NamedTaxItem("PDV", 100, 25, 25)

    assert item1 == item2


def test_named_tax_item_inequality():
    item1 = NamedTaxItem("Tax1", 100, 5, 5)
    item2 = NamedTaxItem("Tax2", 100, 5, 5)
    item3 = NamedTaxItem("Tax1", 100, 4, 4)

    assert item1 != item2
    assert item1 != item3


def test_fee():
    fee = Fee("Misc", 100)

    assert str(fee) == "Misc"
    assert fee.amount == Decimal("100.00")


def test_fee_equality():
    fee1 = Fee("Misc", 100)
    fee2 = Fee("Misc", 100)

    assert fee1 == fee2


def test_fee_inequality():
    fee1 = Fee("Misc", 100)
    fee2 = Fee("Other", 100)
    fee3 = Fee("Misc", 99)

    assert fee1 != fee2
    assert fee1 != fee3
