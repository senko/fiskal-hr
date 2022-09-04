import re
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional, Union
from urllib.parse import urlencode

from .enums import PaymentMethod, SequenceScope
from .item import Fee, TaxItem
from .oib import OIB
from .utils import to_decimal2
from .zki import ZKI

if TYPE_CHECKING:
    from ..ws import FiskalClient

BASE_INVOICE_QR_CHECK_URL = "https://porezna.gov.hr/rn"


class InvoiceNumber:
    """
    Broj Računa

    Must conform to the format <seq>/<loc>/<dev> where <loc> is the location code (alphanumeric),
    <dev> is the ID of the device producing the invoice (integer), and <seq> is the sequence
    number of the invoice on that location or device (see Invoice.sequence_scope).
    """

    sequence_number: int
    """Invoice sequence number issued on the location/device"""

    location_code: str
    """Unique code for the location"""

    device_number: int
    """Unique ID of the device in the location"""

    invoice_number: str
    """Complete invoice number"""

    def __init__(self, value: str):
        if isinstance(value, InvoiceNumber):
            value = value.invoice_number

        self.invoice_number = str(value)

        seq, loc, dev = self._parse(self.invoice_number)
        self.sequence_number = int(seq)
        self.location_code = loc
        self.device_number = int(dev)

    def __str__(self):
        return self.invoice_number

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, InvoiceNumber)
            and self.invoice_number == other.invoice_number
        )

    @staticmethod
    def _parse(value: str):
        m = re.fullmatch(r"(\d+)/([0-9a-zA-Z]+)/(\d+)", value)
        if not m:
            raise ValueError("Invoice number must be in format nnn/ABC/nnn")
        return m.groups()


class BaseDocument:
    """
    Base class for creating documents
    """

    def __init__(self, client: "FiskalClient", **kwargs):
        """
        Create a new Invoice or Document instance

        Args:
            * client - FiskalClient instance for communication to the web service

        Accepts any number of keyword arguments to initialize properties.
        Uninitialized properties are set to None or other default (empty) values.

        Object properties can be set, read and deleted. Deleting them resets them to
        their default (empty) values.
        """

        self.client = client

        # Set each of the settable attributes using provided kwargs, or reset it if
        # it wasn't provided. This ensures the internal attribute backing each property
        # is set. We traverse the inheritance chain to make this work for all of the
        # subclasses.
        for cls in self.__class__.mro():
            for name, attr in cls.__dict__.items():
                if name.startswith("_"):
                    continue

                if isinstance(attr, property) and attr.fset is not None:
                    if name in kwargs:
                        # Set using the provided arg
                        attr.fset(self, kwargs[name])
                    elif attr.fdel is not None:
                        # Initialize with default (empty) value
                        attr.fdel(self)

    @property
    def oib(self) -> Optional[OIB]:
        """
        OIB obveznika fiskalizacije

        Must be equal to the OIB the client certificate is issued to.

        Required
        """
        return self._oib

    @oib.setter
    def oib(self, value: Union[OIB, str]) -> None:
        self._oib = OIB(value)

    @oib.deleter
    def oib(self) -> None:
        self._oib = None

    @property
    def issued_at(self) -> datetime:
        """
        Datum i vrijeme izdavanja

        Required (default: datetime.now())
        """
        return self._issued_at

    @issued_at.setter
    def issued_at(self, value: datetime) -> None:
        self._issued_at = value

    @issued_at.deleter
    def issued_at(self) -> None:
        self._issued_at = datetime.now()

    @property
    def invoice_number(self) -> Optional[InvoiceNumber]:
        """
        Broj računa (broj/prostor/uređaj)

        Required
        """
        return self._invoice_number

    @invoice_number.setter
    def invoice_number(self, value: Union[InvoiceNumber, str]) -> None:
        self._invoice_number = InvoiceNumber(value)

    @invoice_number.deleter
    def invoice_number(self) -> None:
        self._invoice_number = None

    @property
    def total(self) -> Optional[Decimal]:
        """
        Ukupan iznos iskazan na računu ili pratećem dokumentu

        Required
        """

        return self._total

    @total.setter
    def total(self, amount: Decimal) -> None:
        self._total = to_decimal2(amount)

    @total.deleter
    def total(self) -> None:
        self._total = None

    @property
    def is_late_registration(self) -> bool:
        """
        Oznaka naknadne dostave računa

        Required (default: False)
        """
        return self._late_registration

    @is_late_registration.setter
    def is_late_registration(self, is_late: bool) -> None:
        self._late_registration = bool(is_late)

    @is_late_registration.deleter
    def is_late_registration(self) -> None:
        self._late_registration = False

    def calculate_zki(self) -> ZKI:
        """
        Calculate and return ZKI (Zaštitni Kod Izdavatelja)

        Returns:
            * zki
        """

        if self.invoice_number is None:
            raise ValueError("Invoice number is required")

        if self.oib is None:
            raise ValueError("OIB is required")

        if self.total is None:
            raise ValueError("Total invoice amount is required")

        return ZKI.calculate(
            self.oib,
            self.issued_at,
            self.invoice_number,
            self.total,
            self.client.signer,
        )


class Invoice(BaseDocument):
    """
    Invoice data

    See section 2.1. "Račun" in the Fiskalizacija technical specification for
    more information.
    """

    @property
    def vat(self) -> Optional[List[TaxItem]]:
        """
        PDV (porez na dodanu vrijednost)

        Required only if the invoice contains PDV
        """
        return self._vat_items

    @vat.setter
    def vat(self, value: List[TaxItem]) -> None:
        if len(value) == 0:
            raise ValueError("VAT must not be an empty list")
        self._vat_items = value

    @vat.deleter
    def vat(self) -> None:
        self._vat_items = None

    @property
    def consumption_tax(self) -> Optional[List[TaxItem]]:
        """
        PNP (porez na potrošnju)

        Required only if the invoice contains PNP
        """
        return self._ctax_items

    @consumption_tax.setter
    def consumption_tax(self, value: List[TaxItem]) -> None:
        if len(value) == 0:
            raise ValueError("Consumption tax must not be an empty list")
        self._ctax_items = value

    @consumption_tax.deleter
    def consumption_tax(self) -> None:
        self._ctax_items = None

    @property
    def fees(self) -> Optional[List[Fee]]:
        """
        Naknade

        Required only if the invoice contains special fees
        """
        return self._fee_items

    @fees.setter
    def fees(self, value: List[Fee]) -> None:
        if len(value) == 0:
            raise ValueError("Fees must not be an empty list")
        self._fee_items = value

    @fees.deleter
    def fees(self) -> None:
        self._fee_items = None

    @property
    def is_vat_registered(self) -> bool:
        """
        U sustavu PDV

        Required (default: False)
        """
        return self._vat_registered

    @is_vat_registered.setter
    def is_vat_registered(self, value: bool) -> None:
        self._vat_registered = bool(value)

    @is_vat_registered.deleter
    def is_vat_registered(self) -> None:
        self._vat_registered = False

    @property
    def sequence_scope(self) -> SequenceScope:
        """
        Oznaka slijednosti

        Required (default: SequenceScope.LOCATION)
        """
        return self._sequence_scope

    @sequence_scope.setter
    def sequence_scope(self, scope: SequenceScope) -> None:
        self._sequence_scope = scope

    @sequence_scope.deleter
    def sequence_scope(self) -> None:
        self._sequence_scope = SequenceScope.LOCATION

    @property
    def vat_exempt(self) -> Optional[Decimal]:
        """
        Iznos oslobođenja

        Required only if some amount is VAT-exempt
        """
        return self._vat_exempt_amount

    @vat_exempt.setter
    def vat_exempt(self, amount: Decimal) -> None:
        self._vat_exempt_amount = to_decimal2(amount)

    @vat_exempt.deleter
    def vat_exempt(self) -> None:
        self._vat_exempt_amount = None

    @property
    def special_margin_taxation(self) -> Optional[Decimal]:
        """
        Iznos na koji se odnosi poseban postupak oporezivanja marže

        Required only if there is special margin taxation
        """
        return self._margin_taxation_amount

    @special_margin_taxation.setter
    def special_margin_taxation(self, amount: Optional[Decimal]):
        self._margin_taxation_amount = to_decimal2(amount)

    @special_margin_taxation.deleter
    def special_margin_taxation(self) -> None:
        self._margin_taxation_amount = None

    @property
    def tax_exempt_total(self) -> Optional[Decimal]:
        """
        Iznos koji ne podliježe oporezivanju

        Required only if there is tax-exempt amount
        """
        return self._tax_exempt_total

    @tax_exempt_total.setter
    def tax_exempt_total(self, amount: Decimal) -> None:
        self._tax_exempt_total = to_decimal2(amount)

    @tax_exempt_total.deleter
    def tax_exempt_total(self) -> None:
        self._tax_exempt_total = None

    @property
    def payment_method(self) -> PaymentMethod:
        """
        Način plaćanja

        Required (default: PaymentMethod.OTHER)
        """
        return self._payment_method

    @payment_method.setter
    def payment_method(self, method: PaymentMethod) -> None:
        self._payment_method = method

    @payment_method.deleter
    def payment_method(self) -> None:
        self._payment_method = PaymentMethod.OTHER

    @property
    def operator_oib(self) -> Optional[OIB]:
        """
        OIB operatera na naplatnom uređaju

        Required (default: invoice issuer OIB [self.oib])
        """
        return self._operator_oib if self._operator_oib else self.oib

    @operator_oib.setter
    def operator_oib(self, oib: Union[OIB, str]) -> None:
        self._operator_oib = OIB(oib)

    @operator_oib.deleter
    def operator_oib(self) -> None:
        self._operator_oib = None

    @property
    def paragon_number(self) -> Optional[str]:
        """
        Oznaka paragon računa

        Required only if late reporting manually-created (paragon) invoices
        """
        return self._paragon_number

    @paragon_number.setter
    def paragon_number(self, num: str) -> None:
        self._paragon_number = num

    @paragon_number.deleter
    def paragon_number(self) -> None:
        self._paragon_number = None

    def get_ws_object_type(self) -> Any:
        """
        Returns the WSDL type used for this object
        """

        return self.client.type_factory.RacunType

    def to_ws_object(self, original_zki: Optional[ZKI] = None) -> Any:
        """
        Create a WS object based on the invoice attributes

        Args:
            original_zki - optional, if a known ZKI should be used

        ZKI should only be supplied for payment method change operation
        that references an existing invoice.

        Returns:
            tns.RacunType object ready to be sent
        """

        # As a side-effect, this will verify there is minimal info
        # required for the invoice
        zki = self.calculate_zki()

        ws_br_rac = self.client.type_factory.BrojRacunaType(
            BrOznRac=self.invoice_number.sequence_number,
            OznPosPr=self.invoice_number.location_code,
            OznNapUr=self.invoice_number.device_number,
        )

        if self.vat:
            ws_pdv = self.client.type_factory.PdvType(
                Porez=[
                    self.client.type_factory.PorezType(
                        Stopa=item.rate, Osnovica=item.base, Iznos=item.amount
                    )
                    for item in self.vat
                ]
            )
        else:
            ws_pdv = None

        if self.consumption_tax:
            ws_pnp = self.client.type_factory.PorezNaPotrosnjuType(
                Porez=[
                    self.client.type_factory.PorezType(
                        Stopa=item.rate, Osnovica=item.base, Iznos=item.amount
                    )
                    for item in self.consumption_tax
                ]
            )
        else:
            ws_pnp = None

        if self.fees:
            ws_naknade = [
                self.client.type_factory.NaknadaType(
                    NazivN=item.name, IznosN=item.amount
                )
                for item in self.fees
            ]
        else:
            ws_naknade = None

        type_factory = self.get_ws_object_type()

        return type_factory(
            Oib=self.oib,
            USustPdv=self.is_vat_registered,
            DatVrijeme=self.issued_at.strftime("%d.%m.%YT%H:%M:%S"),
            OznSlijed=self.sequence_scope,
            BrRac=ws_br_rac,
            Pdv=ws_pdv,
            Pnp=ws_pnp,
            IznosOslobPdv=self.vat_exempt,
            IznosMarza=self.special_margin_taxation,
            IznosNePodlOpor=self.tax_exempt_total,
            Naknade=ws_naknade,
            IznosUkupno=self.total,
            NacinPlac=self.payment_method,
            OibOper=self.operator_oib,
            ZastKod=original_zki if original_zki else zki,
            NakDost=self.is_late_registration,
            ParagonBrRac=self.paragon_number,
            # See Fiskalizacija Tehnička specifikacija, section 13: Errors
            # error v125: "Trenutno ne postoje 'Ostali porezi'"
            OstaliPor=None,
            # error v141: Polje 'Specifična namjena' je namijenjeno za buduće potrebe.
            SpecNamj=None,
        )

    def get_qr_link(self, jir=None):

        # Calculate ZKI even if JIR is specified so it validates other
        # required elements
        zki = self.calculate_zki()

        params = {
            "izn": str(int(123 * self.total)),
            "datv": self.issued_at.strftime("%Y%m%d_%H%M"),
        }

        if jir:
            params["jir"] = jir
        else:
            params["zki"] = zki

        return f"{BASE_INVOICE_QR_CHECK_URL}?" + urlencode(params)


class InvoiceWithDoc(Invoice):
    """
    Invoice data that contains reference to the accompanying document

    See section 2.1.1.2 in Fiskalizacija technical specification, "Podatkovni
    skup zahtjeva za račun koji se odnosi na prateći dokument (PD)"
    """

    def __init__(self, client: "FiskalClient", **kwargs):
        super().__init__(client, **kwargs)

        self._document_jir = kwargs.get("document_jir")

        if "document_zki" in kwargs:
            self.document_zki = kwargs["document_zki"]
        else:
            del self.document_zki

    @property
    def document_jir(self) -> Optional[str]:
        """
        Jedinstveni identifikator pratećeg dokumenta (JIR PD)

        Required if exists, otherwise `document_zki` is required.
        """
        return self._document_jir

    @document_jir.setter
    def document_jir(self, jir: str) -> None:
        self._document_jir = jir

    @document_jir.deleter
    def document_jir(self) -> None:
        self._document_jir = None

    @property
    def document_zki(self) -> Optional[str]:
        """
        Zaštitni kod izdavatelja za prateći dokument (ZKI PD)

        Required if `document_jri` is not set.
        """
        return self._document_zki

    @document_zki.setter
    def document_zki(self, zki: Union[ZKI, str]) -> None:
        if not isinstance(zki, ZKI):
            zki = ZKI(zki)
        self._document_zki = zki

    @document_zki.deleter
    def document_zki(self) -> None:
        self._document_zki = None

    def get_ws_object_type(self) -> Any:
        return self.client.type_factory.RacunPDType

    def to_ws_object(self) -> Any:
        obj = super().to_ws_object()

        pds = []

        if self.document_jir:
            pds.append(dict(JirPD=self.document_jir))
        elif self.document_zki:
            pds.append(dict(ZastKodPD=self.document_zki))
        else:
            raise ValueError("Either `document_jir` or `document_zki` must be set")

        obj.PrateciDokument = dict(_value_1=pds)
        return obj


class InvoicePaymentMethodChange(Invoice):
    """
    Original invoice data for payment method change operation
    """

    @property
    def new_payment_method(self) -> Optional[PaymentMethod]:
        """
        Promijenjeni način plaćanja

        Required
        """
        return self._new_payment_method

    @new_payment_method.setter
    def new_payment_method(self, method: PaymentMethod) -> None:
        self._new_payment_method = method

    @new_payment_method.deleter
    def new_payment_method(self) -> None:
        self._new_payment_method = None

    @property
    def original_zki(self) -> Optional[ZKI]:
        """

        Zaštitni kod izdavatelja (ZKI) sa izvornog računa

        Required
        """
        return self._original_zki

    @original_zki.setter
    def original_zki(self, zki: ZKI) -> None:
        self._original_zki = zki

    @original_zki.deleter
    def original_zki(self) -> None:
        self._original_zki = None

    def get_ws_object_type(self) -> Any:
        return self.client.type_factory.RacunPNPType

    def to_ws_object(self) -> Any:
        if not self.original_zki:
            raise ValueError("Original ZKI must be set")

        if not self.new_payment_method:
            raise ValueError("New payment method must be set")

        if self.new_payment_method == self.payment_method:
            raise ValueError("New payment method can't be the same as current")

        obj = super().to_ws_object(original_zki=self.original_zki)
        obj.PromijenjeniNacinPlac = self.new_payment_method
        return obj


class Document(BaseDocument):
    """
    Prateći dokument
    """

    def get_ws_object_type(self) -> Any:
        return self.client.type_factory.PrateciDokumentType

    def to_ws_object(self) -> Any:

        type_factory = self.get_ws_object_type()

        # As a side-effect, this will verify there is minimal info
        # required for the invoice
        zki = self.calculate_zki()

        ws_br_pd = self.client.type_factory.BrojPDType(
            BrOznPD=self.invoice_number.sequence_number,
            OznPosPr=self.invoice_number.location_code,
            OznNapUr=self.invoice_number.device_number,
        )

        return type_factory(
            Oib=self.oib,
            DatVrijeme=self.issued_at.strftime("%d.%m.%YT%H:%M:%S"),
            BrPratecegDokumenta=ws_br_pd,
            IznosUkupno=self.total,
            ZastKodPD=zki,
            NakDost=self.is_late_registration,
        )
