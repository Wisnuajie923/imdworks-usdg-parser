"""Independent character-state oracle: no regex, int(text), or usdg imports."""


def parse_reference(text: str) -> int:
    """Accumulate every ASCII digit, then multiply for missing decimal places."""
    if type(text) is not str:
        raise TypeError('expected str')
    if not 1 <= len(text) <= 79:
        raise ValueError('length')
    accumulator = 0
    whole_digits = 0
    fraction_digits = 0
    after_dot = False
    first_was_zero = False
    for character in text:
        if character == '.':
            if after_dot or whole_digits == 0:
                raise ValueError('dot position')
            after_dot = True
            continue
        code = ord(character)
        if not 48 <= code <= 57:
            raise ValueError('non-ASCII digit')
        digit = code - 48
        if after_dot:
            fraction_digits += 1
            if fraction_digits > 6:
                raise ValueError('precision')
        else:
            if whole_digits and first_was_zero:
                raise ValueError('leading zero')
            first_was_zero = whole_digits == 0 and digit == 0
            whole_digits += 1
        accumulator = accumulator * 10 + digit
    if whole_digits == 0 or (after_dot and fraction_digits == 0):
        raise ValueError('missing digits')
    for _ in range(6 - fraction_digits):
        accumulator *= 10
    if accumulator >= 2 ** 256:
        raise ValueError('overflow')
    return accumulator
