from fiskalhr.enums import PaymentMethod, ResponseErrorEnum, SequenceScope


def test_payment_method_str():
    pm = PaymentMethod.CASH

    assert str(pm) == "G"


def test_sequence_scope_str():
    s = SequenceScope.LOCATION

    assert str(s) == "P"


def test_error_docstring():
    err = ResponseErrorEnum.OIB_MISMATCH
    expected = "OIB iz poruke zahtjeva nije jednak OIB-u iz certifikata."

    assert str(err) == expected
