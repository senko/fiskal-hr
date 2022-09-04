import re
from typing import Union


class OIB:
    """Osobni Identifikacijski Broj"""

    value: str

    def __init__(self, oib: Union[str, "OIB"]):

        if isinstance(oib, OIB):
            oib = oib.value

        self._verify(oib)
        self.value = oib

    def __str__(self):
        return self.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, OIB) and self.value == other.value

    @staticmethod
    def _calc_checksum(val: str):
        # See https://regos.hr/app/uploads/2018/07/KONTROLA-OIB-a.pdf

        csum = 10
        for c in val[:10]:
            csum = (int(c) + csum) % 10
            if csum == 0:
                csum = 10
            csum = (csum * 2) % 11

        return (11 - csum) % 10

    @classmethod
    def _verify(cls, val: str):

        if not re.fullmatch(r"\d{11}", val):
            raise ValueError("OIB must have exactly 11 digits")

        csum = cls._calc_checksum(val)
        if csum != int(val[10]):
            raise ValueError(
                f"Incorrect OIB (control digit {val[10]}, expected {csum})"
            )
