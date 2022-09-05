from unittest.mock import Mock

from fiskalhr.enums import ResponseErrorEnum
from fiskalhr.errors import ResponseError, ResponseErrorDetail


def test_parse_error_details():
    f = Mock(
        Greske=Mock(
            Greska=[
                Mock(
                    SifraGreske=ResponseErrorEnum.OIB_MISMATCH.value,
                    PorukaGreske="text",
                ),
            ],
        ),
    )

    details = ResponseErrorDetail.parse_response(f)

    assert len(details) == 1
    assert details[0].code == ResponseErrorEnum.OIB_MISMATCH
    assert details[0].message == "text"
    assert str(details[0]) == "s005: text"


def test_parse_ignores_non_error():
    f = Mock(
        Greske=Mock(
            Greska=[
                Mock(
                    SifraGreske=ResponseErrorEnum.NO_ERROR.value,
                    PorukaGreske="text",
                ),
            ],
        ),
    )

    details = ResponseErrorDetail.parse_response(f)
    assert len(details) == 0


def test_response_error_from_fault_response():
    f = Mock(
        Greske=Mock(
            Greska=[
                Mock(
                    SifraGreske=ResponseErrorEnum.OIB_MISMATCH.value,
                    PorukaGreske="text",
                ),
            ],
        ),
    )

    err = ResponseError.from_fault_response(f)

    assert len(err.details) == 1
    assert err.details[0].code == ResponseErrorEnum.OIB_MISMATCH
