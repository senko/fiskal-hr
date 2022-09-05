import pytest

from fiskalhr.oib import OIB

TEST_VALID_OIB = "12312312316"


def test_correct_oib_passes_validation():
    o = OIB(TEST_VALID_OIB)
    assert str(o) == TEST_VALID_OIB


def test_incorrect_oib_length_fails():
    with pytest.raises(ValueError):
        OIB("123")


def test_incorrect_oib_checksum_fails():
    with pytest.raises(ValueError):
        OIB("12312312312")


def test_oib_cast_to_oib_is_noop():
    o = OIB(OIB(TEST_VALID_OIB))
    assert str(o) == TEST_VALID_OIB
