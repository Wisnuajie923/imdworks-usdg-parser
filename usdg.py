"""Exact six-decimal USDG amounts, using integer arithmetic only."""
import re

SCALE = 1000000
UINT256_MAX = (1 << 256) - 1
MAX_INPUT_LENGTH = 79  # 72 whole digits, dot, six fractional digits.
_INPUT = re.compile(r'(0|[1-9][0-9]*)(?:\.([0-9]{1,6}))?', re.ASCII)


def parse(text: str) -> int:
    """Parse ASCII decimal text to uint256 base units; never round or coerce.

    TypeError: not an exact built-in str. ValueError: grammar, length or range.
    The length check precedes scanning, slicing and integer conversion.
    """
    if type(text) is not str:
        raise TypeError('USDG input must be a str')
    if not 1 <= len(text) <= MAX_INPUT_LENGTH:
        raise ValueError('USDG input length must be 1..79')
    match = _INPUT.fullmatch(text)
    if match is None:
        raise ValueError('invalid USDG grammar')
    whole, fraction = match.groups()
    units = int(whole) * SCALE + (int(fraction.ljust(6, '0')) if fraction else 0)
    if units > UINT256_MAX:
        raise ValueError('USDG amount exceeds uint256')
    return units


def format_units(units: int) -> str:
    """Canonical decimal: no leading zeros or trailing fractional zeros.

    Only exact built-in int is accepted (bool and subclasses are rejected).
    TypeError for wrong types; ValueError for values outside uint256.
    """
    if type(units) is not int:
        raise TypeError('USDG units must be an int, not bool or another type')
    if not 0 <= units <= UINT256_MAX:
        raise ValueError('USDG units must fit uint256')
    whole, fraction = divmod(units, SCALE)
    if fraction == 0:
        return str(whole)
    return f'{whole}.{fraction:06d}'.rstrip('0')
