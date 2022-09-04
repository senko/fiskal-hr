from enum import Enum

from fiskalhr.meta import get_response_error_enum_docstrings


class PaymentMethod(Enum):
    CASH = "G"
    """Gotovina"""

    CARD = "K"
    """Kartica"""

    CHECK = "C"
    """Ček"""

    WIRE = "T"
    """Virmansko plaćanje"""

    OTHER = "O"
    """Ostalo"""

    def __str__(self):
        return self.value


class SequenceScope(Enum):
    LOCATION = "P"
    """Slijednost na nivou poslovnog prostora"""

    DEVICE = "N"
    """Slijednost na nivou naplatnog uređaja"""

    def __str__(self):
        return self.value


class ResponseErrorEnum(Enum):
    @classmethod
    def from_code(cls, code: str) -> "ResponseErrorEnum":
        code_map = {e.value: e for e in cls}
        return code_map.get(code)

    @property
    def message(self) -> str:
        return self._value_docstrings.get(self.value, "")

    def __str__(self) -> str:
        return self.message

    # -- ENUMS START --

    NO_ERROR = "v100"
    "Poruka je ispravna."

    INVALID_XML = "s001"
    """Poruka nije u skladu s XML shemom."""

    INVALID_CLIENT_CERTIFICATE = "s002"
    """Certifikat nije izdan od strane FINA RDC CA ili je istekao ili je ukinut."""

    WRONG_CLIENT_CERTIFICATE_TYPE = "s003"
    """Certifikat ne sadrži naziv 'Fiskal'."""

    INCORRECT_DIGITAL_SIGNATURE = "s004"
    """Neispravan digitalni potpis."""

    OIB_MISMATCH = "s005"
    """OIB iz poruke zahtjeva nije jednak OIB-u iz certifikata."""

    SERVER_ERROR = "s006"
    """Sistemska pogreška prilikom obrade zahtjeva."""

    PAYMENT_METHOD_CHANGE_DATE_MISMATCH = "s007"
    """
    Datum izdavanja računa u poruci promjene načina plaćanja nije jednak trenutnom datumu.
    """

    PAYMENT_METHOD_CHANGE_DATA_DIFFERS_WITH_INVOICE = "s008"
    """
    Podaci za račun u poruci promjene načina plaćanja razlikuju se od podataka
    fiskaliziranog računa ili račun nije fiskaliziran.
    """

    MESSAGE_DATETIME_OUT_OF_BOUNDS = "v101"
    """
    Datum i vrijeme slanja računa je za više od 6 sati manje ili veće od datuma i
    vremena zaprimanja računa u sustav fiskalizacije.
    """

    INVOICE_DATETIME_OUT_OF_BOUNDS = "v103"
    """
    Datum i vrijeme izdavanja računa je za više od 6 sati veće od datuma i vremena
    zaprimanja računa u sustav fiskalizacije.
    """

    INVOICE_ISSUED_AFTER_SENDING = "v104"
    """
    'Datum i vrijeme izdavanja' računa je veće od 'Datum i vrijeme slanja'.

    Oba datuma i vremena se generiraju na strani obveznika. Prvo se generira datum
    i vrijeme izdavanja računa, a tek kasnije datum i vrijeme slanja računa, stoga bi
    datum i vrijeme izdavanja trebao biti manji ili jednak datumu i vremenu slanja
    računa.
    """

    INVALID_INVOICE_SEQUENCE_NUMBER = "v105"
    """
    'Brojčana oznaka računa' ima vrijednost '0'.

    Brojčana oznaka računa ne smije biti manja od broja 1.
    """

    INVOICE_SEQUENCE_NUMBER_TOO_LARGE = "v106"
    """'Brojčana oznaka računa' ima više od 6 znamenki."""

    INVOICE_VAT_RATE_UNKNOWN = "v110"
    """'Porezna stopa PDV-a' nije iz dozvoljenog skupa poreznih stopa."""

    VAT_BASE_GREATER_THAN_TOTAL = "v112"
    """
    'Osnovica PDV-a' je veća od podatka 'Ukupni iznos' kada je 'Ukupni iznos'
    pozitivnog predznaka ili je jednak 0.
    """

    VAT_BASE_LESS_THAN_THAN_TOTAL = "v113"
    """
    ‘Osnovica PDV-a' je manja od podatka 'Ukupni iznos' kada je 'Ukupni iznos'
    negativnog predznaka ili je jednak 0.
    """

    VAT_SIGN_MISMATCH = "v114"
    """
    'Osnovica PDV-a' nije istog predznaka kao i 'Ukupni iznos'.
    """

    VAT_AMOUNT_LESS_THAN_CALCULATED = "v115"
    """
    'Iznos poreza PDV-a' je za više od 1 kn manji od izračuna iznosa PDV-a.
    """

    VAT_AMOUNT_GREATER_THAN_CALCULATED = "v116"
    """
    'Iznos poreza PDV-a' je za više od 1 kn veći od izračuna iznosa poreza PDV-a.
    """

    CTAX_RATE_NEGATIVE = "v117"
    """'Porezna stopa PNP-a' je manja od 0,00."""

    CTAX_RATE_TOO_LARGE = "v118"
    """'Porezna stopa PNP-a' ja veća od 3,00."""

    CTAX_BASE_GREATER_THAN_CALCULATED = "v120"
    """
    'Osnovica PNP-a' je veća od podatka 'Ukupni iznos' kada je 'Ukupni iznos'
    pozitivnog predznaka ili je jednak 0.
    """

    CTAX_BASE_LESS_THAN_CALCULATED = "v121"
    """
    'Osnovica PNP-a' je manja od podatka 'Ukupni iznos' kada je 'Ukupni iznos'
    negativnog predznaka ili je jednak 0.
    """

    CTAX_SIGN_MISMATCH = "v122"
    """
    'Osnovica PNP-a' nije istog predznaka kao i 'Ukupni iznos'.
    """

    CTAX_AMOUNT_LESS_THAN_CALCULATED = "v123"
    """
    'Iznos poreza PNP-a' je za više od 1 kn manji od izračuna iznosa poreza PNP-a.
    """

    CTAX_AMOUNT_GREATER_THAN_CALCULATED = "v124"
    """
    'Iznos poreza PNP-a' je za više od 1 kn veći od izračuna iznosa poreza PNP-a.
    """

    OTHER_TAX_INCLUDED = "v125"
    """
    'Na računu postoji podatak 'Ostali porezi' različit od '0,00'.
    """

    VAT_EXEMPT_AMOUNT_GREATER_THAN_TOTAL = "v126"
    """
    Iznos oslobođenja' je veći od podatka 'Ukupni iznos' kada je 'Ukupni iznos'
    pozitivnog predznaka ili je jednak 0.
    """

    VAT_EXEMPT_AMOUNT_LESS_THAN_TOTAL = "v127"
    """
    Iznos oslobođenja' je manji od podatka 'Ukupni iznos' kada je 'Ukupni iznos'
    negativnog predznaka ili je jednak 0.
    """

    VAT_EXEMPT_SIGN_MISMATCH = "v128"
    """
    Iznos oslobođenja' nije istog predznaka kao i 'Ukupni iznos'.
    """

    MARGIN_TAXATION_AMOUNT_GREATER_THAN_TOTAL = "v129"
    """
    'Iznos marže' je veći od podatka 'Ukupni iznos' kada je 'Ukupni iznos'
    pozitivnog predznaka ili je jednak 0.
    """

    MARGIN_TAXATION_AMOUNT_LESS_THAN_TOTAL = "v130"
    """
    'Iznos marže' je manji od podatka 'Ukupni iznos' kada je 'Ukupni iznos'
    negativnog predznaka ili je jednak 0.
    """

    MARGIN_TAXATION_SIGN_MISMATCH = "v131"
    """
    'Iznos marže' nije istog predznaka kao i 'Ukupni iznos'.
    """

    TAX_EXEMPT_TOTAL_GREATER_THAN_TOTAL = "v132"
    """
    Iznos koji ne podliježe oporezivanju' je veći od podatka 'Ukupni iznos'
    kada je 'Ukupni iznos' pozitivnog predznaka ili je jednak 0.
    """

    TAX_EXEMPT_TOTAL_LESS_THAN_TOTAL = "v133"
    """
    'Iznos koji ne podliježe oporezivanju' je manji od podatka 'Ukupni iznos'
    kada je 'Ukupni iznos' negativnog predznaka ili je jednak 0.
    """

    TAX_EXEMPT_TOTAL_SIGN_MISMATCH = "v134"
    """
    'Iznos koji ne podliježe oporezivanju' nije istog predznaka kao i 'Ukupni iznos'.
    """

    FEE_TOO_LARGE = "v135"
    """
    'Iznos naknade' je veći od 1.000,00 kn.
    """

    FEE_TOO_SMALL = "v136"
    """
    'Iznos naknade' je manji od -1.000,00 kn.
    """

    TOTAL_AMOUNT_DIFFERS_FROM_CALCULATED = "v137"
    """
    'Ukupan iznos na računu' nije ispravan prema formuli.

    Formula za kontrolu ukupnog iznosa je:

        SUM(Iznos osnovica PDV) +
        SUM(Iznos PDV) +
        (Iznos PNP) +
        (Iznos oslobođenja) +
        (Iznos koji ne podliježe oporezivanju) +
        SUM(Iznos naknada).

    Dopuštena tolerancija je +/- 0,01 kuna.
    """

    WIRE_TOTAL_AMOUNT_TOO_LARGE = "v139"
    """
    Maksimalni ukupni iznos za vrstu plaćanja 'Transakcijski račun' i 'Ostalo'
    je veći ili manji od 1 mil kn kada je Ukupni iznos
    pozitivnog/negativnog predznaka.
    """

    SPECIFIC_PURPOSE_NOT_EMPTY = "v141"
    """
    Polje 'Specifična namjena' je namijenjeno za buduće potrebe.
    """

    NONZERO_VAT = "v142"
    """
    Na računu postoji podatak 'PDV' različit od '0,00'.

    Ova provjera se vrši ako je na računu obveznik iskazao da nije u sustavu PDV-a.
    """

    NONZERO_VAT_EXEMPT = "v143"
    """
    Na računu postoji podatak 'Iznos oslobođenja' različit od 0,00 kn.

    Ova provjera se vrši ako je na računu obveznik iskazao da nije u sustavu PDV-a.
    """

    NONZERO_MARGIN_TAXATION = "v144"
    """
    Na računu postoji podatak 'Iznos marže' različit od 0,00 kn.

    Ova provjera se vrši ako je na računu obveznik iskazao da nije u sustavu PDV-a.
    """

    NONZERO_TAX_EXEMPT_TOTAL = "v145"
    """
    Na računu postoji podatak 'Iznos koji ne podliježe oporezivanju' različit od 0,00 kn.

    Ova provjera se vrši ako je na računu obveznik iskazao da nije u sustavu PDV-a.
    """

    CASH_TOTAL_AMOUNT_TOO_LARGE = "v148"
    """
    Maksimalni ukupni iznos za vrstu plaćanja 'Gotovina', 'Kartica' ili 'Ček' je
    veći ili manji od +/-75.000,00 kn kada je Ukupni iznos pozitivnog/negativnog predznaka.
    """

    LATE_INVOICE2 = "v152"
    """
    'Datum i vrijeme izdavanja' računa je za više od 2 dana do zaključno 5 dana manje od
    'Datum i vrijeme obrade'.
    """

    LATE_INVOICE5 = "v153"
    """
    'Datum i vrijeme izdavanja' računa je za više od 5 dana manje od 'Datum i vrijeme obrade'.
    """

    # -- ENUMS END --


ResponseErrorEnum._value_docstrings = get_response_error_enum_docstrings()
