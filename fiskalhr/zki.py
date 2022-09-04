# TODO - missing actual ZKI calculations
import re
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..signature import Signer
    from .invoice import InvoiceNumber
    from .oib import OIB


class ZKI:
    """Zaštitni Kod Izdavatelja"""

    def __init__(self, val: str):
        if not re.fullmatch(r"[0-9a-f]{32}", val):
            raise ValueError(f"Incorrect ZKI format: {val}")
        self.value = val

    @staticmethod
    def calculate(
        oib: "OIB",
        dt: datetime,
        invoice_number: "InvoiceNumber",
        amount: Decimal,
        signer: "Signer",
    ) -> "ZKI":
        """
        Calculate ZKI (invoice control code)

        Args:
            * oib - OIB of the invoicing business
            * dt - date and time of the invoice
            * invoice_number - invoice number
            * amount - exact amount as Decimal with two decimal places
            * signer - Signer instance to sign the ZKI

        Returns:
            *  calculated ZKI

        See Section 12 of Fiskalizacija technical documentation for
        the specification of the algorithm used here.
        """

        payload = "".join(
            [
                str(oib),
                dt.strftime("%d.%m.%Y %H:%M:%S"),
                str(invoice_number.sequence_number),
                invoice_number.location_code,
                str(invoice_number.device_number),
                str(amount),
            ]
        )
        return ZKI(signer.sign_zki_payload(payload))

    def __str__(self):
        return self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ZKI) and self.value == other.value
