import re
from inspect import getsource
from logging import getLogger
from typing import Dict

log = getLogger(__name__)


# Match indented enum in the format:
#     NAME = "value"
#     """docstring"""
# (allowing for multiline docstrings and using only one " in the doc)
ENUM_SOURCE_REGEXP = r'\s+([A-Z0-9_]+)\s+=\s+"([^"]+)"\s+"{1,3}([^"]+)"{1,3}'


def get_response_error_enum_docstrings() -> Dict[str, str]:
    """
    Return docstrings for ResponseErrorEnum values

    Inspects the source code and extracts the docstrings manually,
    since Python doesn't handle enum docstrings.

    Returns:
        * mapping of enum values to docstrings

    Highly sensitive to the source code format, and will intentionally
    crash if the source code is not what it expects. This is to spot
    desync between the code and expectation immediately.
    """
    from .enums import ResponseErrorEnum

    source_code = getsource(ResponseErrorEnum)
    match_enums = re.match(
        r".*# -- ENUMS START --(.*)# -- ENUMS END --.*",
        source_code,
        flags=re.MULTILINE | re.DOTALL,
    )
    enums = match_enums.groups()[0]

    docmap = {}

    for name, code, doc in re.findall(ENUM_SOURCE_REGEXP, enums):
        attr = getattr(ResponseErrorEnum, name)
        assert attr.value == code
        docmap[code] = re.sub(r"\s+", " ", doc).strip()

    assert len(docmap) == len(ResponseErrorEnum)

    return docmap
