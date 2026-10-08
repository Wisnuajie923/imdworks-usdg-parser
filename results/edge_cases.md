# Hand-selected edge cases

Expected decisions and units were written as fixtures before evaluation.

| Input | Expected | Actual | Units / canonical | Reason |
| --- | --- | --- | --- | --- |
| `"0"` | accept | accept | 0 / 0 | Zero |
| `"1"` | accept | accept | 1000000 / 1 | Integer |
| `"0.000001"` | accept | accept | 1 / 0.000001 | Minimum positive amount |
| `"0.999999"` | accept | accept | 999999 / 0.999999 | Below one token |
| `"12.3456"` | accept | accept | 12345600 / 12.3456 | Four decimal places |
| `"1.000000"` | accept | accept | 1000000 / 1 | Six trailing zeros allowed |
| `"0.010000"` | accept | accept | 10000 / 0.01 | Trailing zeros preserve exactness |
| `"0.0"` | accept | accept | 0 / 0 | Noncanonical zero is exact |
| `"1.230000"` | accept | accept | 1230000 / 1.23 | Canonical display removes zeros |
| `"115792089237316195423570985008687907853269984665640564039457584007913129.639935"` | accept | accept | 115792089237316195423570985008687907853269984665640564039457584007913129639935 / 115792089237316195423570985008687907853269984665640564039457584007913129.639935 | uint256 maximum |
| `"115792089237316195423570985008687907853269984665640564039457584007913129.639934"` | accept | accept | 115792089237316195423570985008687907853269984665640564039457584007913129639934 / 115792089237316195423570985008687907853269984665640564039457584007913129.639934 | One unit below maximum |
| `"115792089237316195423570985008687907853269984665640564039457584007913129.639936"` | reject | reject | — | One unit above maximum |
| `"115792089237316195423570985008687907853269984665640564039457584007913130"` | reject | reject | — | Whole amount over maximum |
| `""` | reject | reject | — | Empty |
| `"00"` | reject | reject | — | Leading zero |
| `"01"` | reject | reject | — | Leading zero |
| `"00.1"` | reject | reject | — | Fraction does not excuse leading zero |
| `"+1"` | reject | reject | — | Plus sign |
| `"-1"` | reject | reject | — | Minus sign |
| `"-0"` | reject | reject | — | Signed zero |
| `" 1"` | reject | reject | — | Leading space |
| `"1 "` | reject | reject | — | Trailing space |
| `"\t1"` | reject | reject | — | Tab |
| `"1\n"` | reject | reject | — | Trailing LF |
| `"1\r\n"` | reject | reject | — | Trailing CRLF |
| `".1"` | reject | reject | — | Missing whole digits |
| `"1."` | reject | reject | — | Missing fractional digits |
| `"1..2"` | reject | reject | — | Repeated dot |
| `"1e3"` | reject | reject | — | Exponent |
| `"1E-6"` | reject | reject | — | Exponent |
| `"0.0000001"` | reject | reject | — | Excess nonzero precision |
| `"1.0000000"` | reject | reject | — | Excess zero precision |
| `"\u0661"` | reject | reject | — | Arabic-Indic digit |
| `"\uff11"` | reject | reject | — | Fullwidth digit |
| `"\ud835\udfd9"` | reject | reject | — | Mathematical digit |
| `"1\uff0e0"` | reject | reject | — | Fullwidth dot |
| `"1\u00a0"` | reject | reject | — | Nonbreaking space |
| `"1\u200b"` | reject | reject | — | Zero-width space |
| `"1_000"` | reject | reject | — | Underscore |
| `"1,000"` | reject | reject | — | Thousands separator |
| `"0x10"` | reject | reject | — | Hexadecimal |
| `"NaN"` | reject | reject | — | NaN |
| `"Infinity"` | reject | reject | — | Infinity |
| `"1\u0000"` | reject | reject | — | NUL |
| `"99999999999999999999999999999999999999999999999999999999999999999999999999999999"` | reject | reject | — | Overlength |
| `"1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"` | reject | reject | — | Huge malformed input |
