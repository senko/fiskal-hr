from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from fiskalhr.invoice import InvoiceNumber
from fiskalhr.oib import OIB
from fiskalhr.zki import ZKI


def test_zki_constructor_str():
    raw = "abcd" * 8
    z = ZKI(raw)
    assert str(z) == raw


def test_zki_constructor_checks_length():
    with pytest.raises(ValueError):
        ZKI("123")


def test_zki_constructor_checks_xdigits():
    with pytest.raises(ValueError):
        ZKI("xywz" * 8)


def test_zki_calculate():
    signer = Mock()

    signer.sign_zki_payload.return_value = "abcd" * 8

    z = ZKI.calculate(
        OIB("12312312316"),
        datetime.now(),
        InvoiceNumber("1/X/1"),
        Decimal("100"),
        signer,
    )

    signer.sign_zki_payload.assert_called_once()
    assert str(z) == "abcd" * 8


def test_zki_equality():
    assert ZKI("abcd" * 8) == ZKI("abcdabcd" * 4)


def test_zki_inequality():
    assert ZKI("abcd" * 8) != ZKI("1234" * 8)
