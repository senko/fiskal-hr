from typing import List

from .enums import ResponseErrorEnum


class ResponseErrorDetail:
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"

    @classmethod
    def parse_response(cls, response) -> List["ResponseErrorDetail"]:
        return [
            ResponseErrorDetail(
                ResponseErrorEnum.from_code(item.SifraGreske),
                item.PorukaGreske,
            )
            for item in response.Greske.Greska
            if item.SifraGreske != ResponseErrorEnum.NO_ERROR.value
        ]


class ResponseError(Exception):
    def __init__(self, details):
        self.message = "Service error"
        self.details = details

    def __str__(self) -> str:
        return f"{self.message}: " + ",".join(
            detail.code.value for detail in self.details
        )

    @classmethod
    def from_fault_response(cls, fault_response):
        error_details = ResponseErrorDetail.parse_response(fault_response)
        return cls(error_details)
