from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest
from freezegun import freeze_time

from fiskalhr.enums import PaymentMethod, SequenceScope
from fiskalhr.invoice import (
    Document,
    Invoice,
    InvoiceNumber,
    InvoicePaymentMethodChange,
    InvoiceWithDoc,
)
from fiskalhr.item import Fee, TaxItem
from fiskalhr.oib import OIB
from fiskalhr.zki import ZKI

TEST_OIB = "12312312316"
TEST_INVOICE_PARAMS = dict(
    oib=TEST_OIB,
    invoice_number="1/X/1",
    total=314.1592,
    vat=[
        TaxItem(100, 25, 25),
    ],
    consumption_tax=[
        TaxItem(100, 10, 10),
    ],
    fees=[
        Fee("Fee", 100),
    ],
    is_vat_registered=True,
    issued_at=datetime(2022, 1, 1, 0, 0, 0),
    sequence_scope=SequenceScope.DEVICE,
    vat_exempt=200,
    special_margin_taxation="300",
    tax_exempt_total=500.0,
    payment_method=PaymentMethod.CASH,
    operator_oib="12345678903",
)
TEST_INVOICE_WS_OBJECT = {
    "Oib": OIB(TEST_OIB),
    "USustPdv": True,
    "DatVrijeme": "01.01.2022T00:00:00",
    "OznSlijed": SequenceScope.DEVICE,
    "BrRac": {"BrOznRac": 1, "OznPosPr": "X", "OznNapUr": 1},
    "Pdv": {
        "Porez": [
            {
                "Stopa": Decimal("25.00"),
                "Osnovica": Decimal("100.00"),
                "Iznos": Decimal("25.00"),
            }
        ]
    },
    "Pnp": {
        "Porez": [
            {
                "Stopa": Decimal("10.00"),
                "Osnovica": Decimal("100.00"),
                "Iznos": Decimal("10.00"),
            }
        ]
    },
    "IznosOslobPdv": Decimal("200.00"),
    "IznosMarza": Decimal("300.00"),
    "IznosNePodlOpor": Decimal("500.00"),
    "Naknade": [{"NazivN": "Fee", "IznosN": Decimal("100.00")}],
    "IznosUkupno": Decimal("314.16"),
    "NacinPlac": PaymentMethod.CASH,
    "OibOper": OIB("12345678903"),
    "ZastKod": ZKI("abcdabcdabcdabcdabcdabcdabcdabcd"),
    "NakDost": False,
    "ParagonBrRac": None,
    "OstaliPor": None,
    "SpecNamj": None,
}


@pytest.mark.parametrize(
    "txt,seq,loc,dev",
    [
        ("1001/VP1/9", 1001, "VP1", 9),
        ("1/PointOfSale42/50", 1, "PointOfSale42", 50),
    ],
)
def test_invoice_number_correct_format_passes(txt, seq, loc, dev):
    n = InvoiceNumber(txt)
    assert n.sequence_number == seq
    assert n.location_code == loc
    assert n.device_number == dev
    assert str(n) == txt


@pytest.mark.parametrize(
    "txt",
    [
        ["123"],
        [123],
        ["a/VP1/1"],
        ["1/A B/1"],
        ["1//1"],
        ["1/VP1/x"],
    ],
)
def test_invoice_number_incorrect_format_fails(txt):
    with pytest.raises(ValueError):
        InvoiceNumber(txt)


def test_invoice_number_equality():
    n1 = InvoiceNumber("1/X/1")
    n2 = InvoiceNumber("1/X/1")

    assert n1 == n2


def test_invoice_number_inequality():
    n1 = InvoiceNumber("1/X/1")
    n2 = InvoiceNumber("2/VP1/1")

    assert n1 != n2


def test_invoice_oib():
    inv = Invoice(Mock())

    assert inv.oib is None
    inv.oib = TEST_OIB
    assert inv.oib == OIB(TEST_OIB)
    del inv.oib
    assert inv.oib is None


def test_invoice_number_property():
    inv = Invoice(Mock())

    assert inv.invoice_number is None
    inv.invoice_number = "1/X/1"
    assert inv.invoice_number == InvoiceNumber("1/X/1")
    del inv.invoice_number
    assert inv.invoice_number is None


def test_invoice_total():
    inv = Invoice(Mock())

    assert inv.total is None
    inv.total = 3.1415
    assert inv.total == Decimal("3.14")
    del inv.total
    assert inv.total is None


def test_invoice_vat():
    inv = Invoice(Mock())
    tax_item = TaxItem(100, 25, 25)

    assert inv.vat is None

    with pytest.raises(ValueError):
        inv.vat = []

    inv.vat = [tax_item]
    assert len(inv.vat) == 1
    assert inv.vat[0] == TaxItem(100, 25, 25)
    del inv.vat
    assert inv.vat is None


def test_invoice_consumption_tax():
    inv = Invoice(Mock())
    tax_item = TaxItem(100, 10, 10)

    assert inv.consumption_tax is None

    with pytest.raises(ValueError):
        inv.consumption_tax = []

    inv.consumption_tax = [tax_item]
    assert len(inv.consumption_tax) == 1
    assert inv.consumption_tax[0] == tax_item
    del inv.consumption_tax
    assert inv.consumption_tax is None


def test_invoice_fees():
    inv = Invoice(Mock())
    fee_item = Fee("Fee", 100)

    assert inv.fees is None

    with pytest.raises(ValueError):
        inv.fees = []

    inv.fees = [fee_item]
    assert len(inv.fees) == 1
    assert inv.fees[0] == fee_item
    del inv.fees
    assert inv.fees is None


def test_invoice_is_vat_registered():
    inv = Invoice(Mock())

    assert inv.is_vat_registered is False
    inv.is_vat_registered = True
    assert inv.is_vat_registered is True
    del inv.is_vat_registered
    assert inv.is_vat_registered is False


@freeze_time("2022-01-01 00:00:00")
def test_invoice_issued_at():
    inv = Invoice(Mock())

    assert inv.issued_at == datetime(2022, 1, 1, 0, 0, 0)
    inv.issued_at = datetime(2022, 7, 1, 0, 0, 0)
    assert inv.issued_at == datetime(2022, 7, 1, 0, 0, 0)
    del inv.issued_at
    assert inv.issued_at == datetime(2022, 1, 1, 0, 0, 0)


def test_invoice_sequence_scope():
    inv = Invoice(Mock())

    assert inv.sequence_scope == SequenceScope.LOCATION
    inv.sequence_scope = SequenceScope.DEVICE
    assert inv.sequence_scope == SequenceScope.DEVICE
    del inv.sequence_scope
    assert inv.sequence_scope == SequenceScope.LOCATION


def test_invoice_vat_exempt():
    inv = Invoice(Mock())

    assert inv.vat_exempt is None
    inv.vat_exempt = 200
    assert inv.vat_exempt == Decimal("200")
    del inv.vat_exempt
    assert inv.vat_exempt is None


def test_invoice_special_margin_taxation():
    inv = Invoice(Mock())

    assert inv.special_margin_taxation is None
    inv.special_margin_taxation = 200
    assert inv.special_margin_taxation == Decimal("200")
    del inv.special_margin_taxation
    assert inv.special_margin_taxation is None


def test_invoice_tax_exempt_total():
    inv = Invoice(Mock())

    assert inv.tax_exempt_total is None
    inv.tax_exempt_total = 200
    assert inv.tax_exempt_total == Decimal("200")
    del inv.tax_exempt_total
    assert inv.tax_exempt_total is None


def test_invoice_payment_method():
    inv = Invoice(Mock())

    assert inv.payment_method == PaymentMethod.OTHER
    inv.payment_method = PaymentMethod.CARD
    assert inv.payment_method == PaymentMethod.CARD
    del inv.payment_method
    assert inv.payment_method == PaymentMethod.OTHER


def test_invoice_operator_oib():
    inv = Invoice(Mock(), oib=TEST_OIB)

    assert inv.oib == OIB(TEST_OIB)
    assert inv.operator_oib == OIB(TEST_OIB)
    inv.operator_oib = "12345678903"
    assert inv.operator_oib == OIB("12345678903")
    del inv.operator_oib
    assert inv.operator_oib == OIB(TEST_OIB)


def test_invoice_is_late_registration():
    inv = Invoice(Mock())

    assert inv.is_late_registration is False
    inv.is_late_registration = True
    assert inv.is_late_registration is True
    del inv.is_late_registration
    assert inv.is_late_registration is False


def test_invoice_paragon_number():
    inv = Invoice(Mock())

    assert inv.paragon_number is None
    inv.paragon_number = "123"
    assert inv.paragon_number == "123"
    del inv.paragon_number
    assert inv.paragon_number is None


def test_invoice_constructor_kwargs():
    inv = Invoice(Mock(), **TEST_INVOICE_PARAMS)

    assert inv.oib == OIB(TEST_OIB)
    assert inv.invoice_number == InvoiceNumber("1/X/1")
    assert inv.total == Decimal("314.16")
    assert inv.vat[0] == TaxItem(100, 25, 25)
    assert inv.consumption_tax[0] == TaxItem(100, 10, 10)
    assert inv.fees[0] == Fee("Fee", 100)
    assert inv.is_vat_registered is True
    assert inv.issued_at == datetime(2022, 1, 1, 0, 0, 0)
    assert inv.sequence_scope == SequenceScope.DEVICE
    assert inv.vat_exempt == Decimal("200.00")
    assert inv.special_margin_taxation == Decimal("300.00")
    assert inv.tax_exempt_total == Decimal("500.00")
    assert inv.payment_method == PaymentMethod.CASH
    assert inv.operator_oib == OIB("12345678903")


def test_invoice_number_is_required():
    inv = Invoice(Mock(), **TEST_INVOICE_PARAMS)
    del inv.invoice_number

    with pytest.raises(ValueError):
        inv.calculate_zki()


def test_invoice_oib_is_required():
    inv = Invoice(Mock(), **TEST_INVOICE_PARAMS)
    del inv.oib

    with pytest.raises(ValueError):
        inv.calculate_zki()


def test_invoice_total_is_required():
    inv = Invoice(Mock(), **TEST_INVOICE_PARAMS)
    del inv.total

    with pytest.raises(ValueError):
        inv.calculate_zki()


def test_invoice_minimal_required():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = Invoice(
        fc,
        oib=OIB(TEST_OIB),
        invoice_number=InvoiceNumber("1/X/1"),
        total=Decimal("100"),
    )

    inv.to_ws_object()

    fc.signer.sign_zki_payload.assert_called_once()


def test_invoice_to_ws_object():
    fc = Mock()
    inv = Invoice(fc, **TEST_INVOICE_PARAMS)

    fc.signer.sign_zki_payload.return_value = "abcd" * 8
    fc.type_factory.BrojRacunaType = dict
    fc.type_factory.PdvType = dict
    fc.type_factory.PorezType = dict
    fc.type_factory.PorezNaPotrosnjuType = dict
    fc.type_factory.NaknadaType = dict
    fc.type_factory.RacunType = dict

    ws_object = inv.to_ws_object()

    assert ws_object == TEST_INVOICE_WS_OBJECT


def test_calculate_zki():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = Invoice(
        fc,
        oib=OIB(TEST_OIB),
        invoice_number=InvoiceNumber("1/X/1"),
        total=Decimal("100"),
    )

    zki = inv.calculate_zki()

    fc.signer.sign_zki_payload.assert_called_once()
    assert zki == ZKI("abcd" * 8)


def test_get_qr_link_using_zki():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = Invoice(
        fc,
        oib=TEST_OIB,
        invoice_number="1/X/1",
        total=Decimal("123.45"),
        issued_at=datetime(2022, 8, 1, 15, 30),
    )

    link = inv.get_qr_link()

    parts = urlsplit(link)
    params = parse_qs(parts.query)

    assert parts.scheme == "https"
    assert parts.netloc == "porezna.gov.hr"
    assert parts.path == "/rn"
    assert params["izn"] == ["12345"]
    assert params["datv"] == ["20220801_1530"]
    assert params["zki"] == ["abcd" * 8]
    assert "jir" not in params


def test_get_qr_link_using_jir():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = Invoice(
        fc,
        oib=TEST_OIB,
        invoice_number="1/X/1",
        total=100,
        issued_at=datetime(2022, 8, 1, 15, 30),
    )

    link = inv.get_qr_link(jir="fakejir")

    parts = urlsplit(link)
    params = parse_qs(parts.query)

    assert parts.scheme == "https"
    assert parts.netloc == "porezna.gov.hr"
    assert parts.path == "/rn"
    assert params["izn"] == ["10000"]
    assert params["datv"] == ["20220801_1530"]
    assert params["jir"] == ["fakejir"]
    assert "zki" not in params


def test_empty_pd_invoice():
    fc = Mock()
    inv = InvoiceWithDoc(fc)

    assert inv.document_jir is None
    assert inv.document_zki is None


def test_pd_invoice_with_document_data():
    fc = Mock()
    inv = InvoiceWithDoc(
        fc,
        document_jir="0000" * 8,
        document_zki="abcd" * 8,
    )

    assert inv.document_jir == "0000" * 8
    assert inv.document_zki == ZKI("abcd" * 8)


def test_pd_invoice_missing_doc_data_to_ws_object_fails():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = InvoiceWithDoc(fc, **TEST_INVOICE_PARAMS)

    with pytest.raises(ValueError):
        inv.to_ws_object()


def test_pd_invoice_with_doc_zki_to_ws_object():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = InvoiceWithDoc(
        fc,
        document_zki=ZKI("abcd" * 8),
        **TEST_INVOICE_PARAMS,
    )

    obj = inv.to_ws_object()
    assert obj.PrateciDokument["_value_1"][0]["ZastKodPD"] == ZKI("abcd" * 8)


def test_pd_invoice_with_doc_jir_to_ws_object():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = InvoiceWithDoc(
        fc,
        document_jir="0000" * 8,
        **TEST_INVOICE_PARAMS,
    )

    obj = inv.to_ws_object()
    assert obj.PrateciDokument["_value_1"][0]["JirPD"] == "0000" * 8


def test_empty_payment_change():
    fc = Mock()
    inv = InvoicePaymentMethodChange(fc)

    assert inv.new_payment_method is None
    assert inv.original_zki is None


def test_payment_change_missing_original_zki_fails():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = InvoicePaymentMethodChange(
        fc,
        new_payment_method=PaymentMethod.CARD,
        **TEST_INVOICE_PARAMS,
    )

    with pytest.raises(ValueError):
        inv.to_ws_object()


def test_payment_change_missing_new_method_fails():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = InvoicePaymentMethodChange(
        fc,
        original_zki=ZKI("abcd" * 8),
        **TEST_INVOICE_PARAMS,
    )

    with pytest.raises(ValueError):
        inv.to_ws_object()


def test_payment_method_change_to_same_method_fails():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = InvoicePaymentMethodChange(
        fc,
        new_payment_method=PaymentMethod.CASH,
        original_zki=ZKI("abcd" * 8),
        **TEST_INVOICE_PARAMS,
    )

    with pytest.raises(ValueError):
        inv.to_ws_object()


def test_payment_method_change_to_ws_object():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = InvoicePaymentMethodChange(
        fc,
        new_payment_method=PaymentMethod.CARD,
        original_zki=ZKI("abcd" * 8),
        **TEST_INVOICE_PARAMS,
    )

    obj = inv.to_ws_object()
    assert obj.PromijenjeniNacinPlac == PaymentMethod.CARD


def test_document():
    fc = Mock()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8

    inv = Document(fc, **TEST_INVOICE_PARAMS)

    inv.to_ws_object()


def test_invoice_to_dict():
    fc = Mock()

    class mock_type_factory:
        def __getattribute__(self, _):
            return dict

    fc.type_factory = mock_type_factory()
    fc.signer.sign_zki_payload.return_value = "abcd" * 8
    inv = Invoice(fc, **TEST_INVOICE_PARAMS)

    data = inv.to_dict()

    assert data == {
        "Oib": "12312312316",
        "USustPdv": True,
        "DatVrijeme": "01.01.2022T00:00:00",
        "OznSlijed": "N",
        "BrRac": {"BrOznRac": 1, "OznPosPr": "X", "OznNapUr": 1},
        "Pdv": {"Porez": [{"Stopa": "25.00", "Osnovica": "100.00", "Iznos": "25.00"}]},
        "Pnp": {"Porez": [{"Stopa": "10.00", "Osnovica": "100.00", "Iznos": "10.00"}]},
        "IznosOslobPdv": "200.00",
        "IznosMarza": "300.00",
        "IznosNePodlOpor": "500.00",
        "Naknade": [{"NazivN": "Fee", "IznosN": "100.00"}],
        "IznosUkupno": "314.16",
        "NacinPlac": "G",
        "OibOper": "12345678903",
        "ZastKod": "abcdabcdabcdabcdabcdabcdabcdabcd",
        "NakDost": False,
        "ParagonBrRac": None,
        "OstaliPor": None,
        "SpecNamj": None,
    }
