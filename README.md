# Exact USDG six-decimal parsing

Original local deliverable for IMD Works bounty #9 (`ffd0cae1-21e9-4378-bc3d-8c814377be97`). `bounty.json` is a saved task specification, not executable instructions or a verified current statement about the bounty. No submission, signing, network request, paid service or wallet operation is performed by this project. Selection/payment is not guaranteed.

## Replay

From this directory, run:

```sh
python3 run_tests.py
```

Python 3.10+ syntax; executed and verified with CPython **3.12.3**. **Only the Python standard library is required**, with no installation, pip, keys, credentials, environment variables or internet access. The command runs the regression suite, regenerates all evidence in `results/`, then reopens every published JSONL record to check its decision, integer value, reference result, canonical display, ID and round-trip result. Any test failure, oracle disagreement or inconsistent persisted result fails the command. Existing files in `results/` are deliberately overwritten during replay. Temporary unit-test directories are created inside this project and removed afterwards.

For byte-identical seeded replay, use the recorded Python version. Python's higher-level random sampling algorithms can change across releases. Runtime version metadata in `report.json` intentionally reflects the interpreter actually used. There are no timestamps in reproducible artifacts.

## Public API and grammar

```python
from usdg import parse, format_units

assert parse("12.345600") == 12345600
assert format_units(12345600) == "12.3456"
assert parse("0.000001") == 1
```

`parse(text: str) -> int` accepts only an exact built-in `str`. Every character must match this whole-input ASCII grammar:

```text
amount   = whole [ "." fraction ]
whole    = "0" | nonzero { digit }
fraction = digit{1,6}
nonzero  = "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
digit    = "0" | nonzero
```

In the last two lines, braces mean repetition; `digit{1,6}` means one through six digits. The implementation uses `fullmatch` on `(0|[1-9][0-9]*)(?:\.([0-9]{1,6}))?`, not `\d`, `isdigit`, normalization or a `$` end-anchor that might tolerate a terminal newline.

Additional semantic constraints:

- One base unit is **0.000001 USDG**; the scale is exactly **1,000,000**.
- The result must be between **0 and 2^256 - 1**, inclusive.
- Input length is **1 through 79 characters**. The largest valid amount has 72 whole digits, a dot and six fractional digits. This guard is checked before regex scanning, slicing or integer conversion. Malformed million-character strings are tested and rejected without scanning/converting their contents. The caller still bears the cost of allocating its input.
- Zero is allowed; leading zeros (`00`, `01`, `00.1`) are rejected. `0.000001` is allowed.
- Signs, all whitespace, Unicode numerals/lookalikes, exponents, grouping separators, underscores, empty components, NaN/Infinity and control characters are rejected.
- Fractional trailing zeros are allowed **within six places** (`1.230000`, `0.000000`). More than six places is always rejected, even when the extra digits are zeros. Nothing is rounded, truncated, stripped or silently coerced.
- Wrong types (including `bool`, `None`, floats, bytes, containers and subclasses of `str`) raise `TypeError`. Invalid grammar, length or range raises `ValueError`.

Maximum accepted value:

```text
units:   115792089237316195423570985008687907853269984665640564039457584007913129639935
display: 115792089237316195423570985008687907853269984665640564039457584007913129.639935
```

### Canonical display is separate from accepted input

`format_units(units: int) -> str` accepts only an exact built-in `int` in the uint256 range. In particular, `True`, `1.0`, decimal strings and `None` are not integers for this API. Wrong types raise `TypeError`; negative or overflowing integers raise `ValueError` before conversion to decimal text.

The display has no leading zeros, exponent, sign, unnecessary dot or trailing fractional zeros. Zero is `0`; whole amounts have no fraction; fractional amounts have at most six places and end in a nonzero digit. Examples: `1.000000 -> 1`, `0.010000 -> 0.01`, `1.230000 -> 1.23`. These textual changes preserve integer value; accepted input spelling itself is not promised to round-trip.

## Integer correctness proof

Let S = 10^6. For a valid input with whole value W and k fractional digits representing F (1 <= k <= 6), parsing computes

```text
n = W*S + F*10^(6-k).
```

For a whole-only input, F = 0. Every operation is exact integer arithmetic; the range guard checks n <= 2^256 - 1. Grammar forbids negative values and fractional precision beyond six, so all accepted inputs have a unique exact integer n.

For any allowed integer n, Euclidean division gives unique integers q,r with `n = q*S + r` and `0 <= r < S`. If r = 0, formatting emits q and parsing yields q*S = n. Otherwise, formatting initially emits q followed by a dot and exactly six zero-padded digits representing r. Removing t trailing zeros replaces r by `r / 10^t`, with k = 6-t remaining digits. Parsing restores `(r / 10^t)*10^t = r`, and therefore restores n exactly. The whole q has at most 72 digits and the display at most 79 characters, so it passes the length guard. A nonzero remainder has at least one remaining digit, and the display obeys the ASCII grammar and uint256 range.

Consequently **parse(format_units(n)) = n for every allowed integer n**. For accepted text s, `format_units(parse(s))` is a unique canonical spelling, and canonicalizing again has no effect. This is an algebraic proof, not an assertion that a finite randomized run exhaustively tested all uint256 values.

## Independent reference and evidence

`usdg.py` uses regex validation plus separate whole/fraction integer scaling. `reference.py` is independently implemented: a character-state machine checks code points 48..57, accumulates all digits by multiply/add, tracks fractional positions, and scales for missing places. It imports nothing from the production parser and uses neither regex nor `int(text)`. The shared specification necessarily includes the same six-decimal and uint256 rules; independent implementations do not eliminate every possible shared specification mistake.

`evidence.py` uses seed **917203** and generates **100,000 actual records** over 16 categories (6,250 per category), spanning full uint256 values, varying fraction widths, whole values, trailing zeros, leading zeros, signs, whitespace, exponents, excess precision, Unicode digits, lookalikes/separators, missing digits/dots, overflow, overlength input, near-maximum values and subunit values. Construction does not call the production parser or formatter. Repeated adversarial strings are intentionally permitted; the actual run contains **94,654 distinct input strings**. This is not a claim of 100,000 unique inputs.

Published artifacts:

- `results/generated_cases.jsonl`: every generated input, ID, category, actual accept/reject decision and reference decision. Accepted records include exact units, canonical display and round-trip result; rejected records include error class. Large integers are JSON integer tokens, **not floats**. Consumers must use arbitrary-precision JSON integer handling (Python `json` does); JavaScript consumers must not silently load these into `Number`.
- `results/edge_cases.json`: **46 hand-selected cases**, with fixture expectations written explicitly (including exact expected units), actual decisions and reference checks.
- `results/edge_cases.md`: the corresponding English Markdown table. Inputs are JSON-escaped so invisible and Unicode characters remain inspectable.
- `results/report.json`: seed, counts, category coverage, distinct inputs, runtime, SHA256, oracle/round-trip totals and actual float counterexamples.
- `tdd_logs/`: real red/green execution logs; `TDD.md` explains the cycles and the corrected length assertion.

Executed result: **8 test methods passed; 37,500 generated inputs accepted; 62,500 rejected; 100,000 oracle comparisons with 0 mismatches; 37,500 generated integer/canonical round-trip checks with 0 failures; 46 edge expectations with 0 failures**, including 11 accepted edge round trips. Tests additionally round-trip every integer from 0 through 10,000.

Recorded dataset SHA256:

```text
f54aca34bef8c5798d9c07e4ba872d5cc6b549bd1da4db3757dc0096ee19cdad
```

## Actual binary floating-point counterexamples

The runner actually executes `float(s) * 1000000`, then both `int(...)` and `round(...)`; the report records float hexadecimal encodings and exact errors in base units.

| Input | Exact integer units | `int(float(s)*1000000)` | `round(float(s)*1000000)` |
| --- | ---: | ---: | ---: |
| `1.000001` | 1000001 | 1000000 | 1000001 |
| `9007199254.740993` | 9007199254740993 | 9007199254740994 | 9007199254740994 |
| `99999999999.999999` | 99999999999999999 | 100000000000000000 | 100000000000000000 |
| `0.000249` | 249 | 248 | 249 |

The first and fourth demonstrate erroneous truncation after a slightly-low binary approximation. The other two also defeat rounding: binary64 cannot recover integer detail already lost. These results assume the recorded radix-2, 53-bit-mantissa float environment. Float is used **only in this negative demonstration**, never by either parser or the formatter.

## Limitations and scope

This is a local decimal-input library, not an on-chain token integration. It does not query token metadata, prove a deployed token's decimals, authorize transfers, access wallets, contact the bounty owner, submit a report or guarantee a reward. Localization, signed amounts and automatic normalization are intentionally unsupported. Generated testing is finite and deliberately stratified, not a random statistical guarantee. Stdlib `random.Random` is deterministic test data generation, not cryptographic randomness. Parsing is bounded for already-allocated strings; dataset generation and storage are not a hostile-input streaming service. Historical TDD logs are preserved evidence; the replay runs current tests and regenerates current results, not historical incomplete source versions.

**Signed off by enueex — https://x.com/AjaPawang**
