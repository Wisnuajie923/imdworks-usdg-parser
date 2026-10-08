"""Seeded local-only evidence generation. All dependencies are standard library."""
import random
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from reference import parse_reference
from usdg import parse, format_units

SEED = 917203
CASE_COUNT = 100000


def generated_cases(seed=SEED, count=CASE_COUNT):
    """Generate varied text without calling the production parser or formatter.

    Cycle categories for guaranteed coverage; seed affects amounts and mutations.
    Boundary arithmetic is constructed here, not imported from the parser.
    """
    rng = random.Random(seed)
    maximum = 2 ** 256 - 1
    for index in range(count):
        n = rng.randrange(maximum + 1)
        whole, fraction = divmod(n, 10 ** 6)
        valid = f'{whole}.{fraction:06d}'
        small = str(rng.randrange(10 ** 18))
        mode = index % 16
        if mode == 0:
            category, text = 'full_uint256', valid
        elif mode == 1:
            category, text = 'fraction_widths', small + '.' + ''.join(str(rng.randrange(10)) for _ in range(rng.randrange(1, 7)))
        elif mode == 2:
            category, text = 'integers', small
        elif mode == 3:
            category, text = 'trailing_fraction_zeros', small + '.' + str(rng.randrange(1, 10)) + '0' * rng.randrange(1, 6)
        elif mode == 4:
            category, text = 'leading_zeros', '0' + valid
        elif mode == 5:
            category, text = 'signs', rng.choice(['+', '-']) + small
        elif mode == 6:
            category, text = 'whitespace', rng.choice([' ', '\t', '\n', '\r', '\u00a0']) + small
        elif mode == 7:
            category, text = 'exponents', small + rng.choice(['e', 'E']) + str(rng.randrange(-20, 20))
        elif mode == 8:
            category, text = 'excess_precision', small + '.' + ''.join(str(rng.randrange(10)) for _ in range(rng.randrange(7, 13)))
        elif mode == 9:
            category, text = 'unicode_digits', small.translate(str.maketrans('0123456789', rng.choice(['０１２３４５６７８９', '٠١٢٣٤٥٦٧٨٩', '𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡'])))
        elif mode == 10:
            category, text = 'lookalikes_and_separators', small + rng.choice(['．', ',', '_', '\x00', '/', '\u200b']) + '1'
        elif mode == 11:
            category, text = 'missing_digits_or_dots', rng.choice(['.' + small, small + '.', small + '..1', ''])
        elif mode == 12:
            over = maximum + rng.randrange(1, 1000000)
            q, r = divmod(over, 1000000)
            category, text = 'overflow', f'{q}.{r:06d}'
        elif mode == 13:
            category, text = 'long_malformed', rng.choice(['9', 'x', '０']) * rng.randrange(80, 1025)
        elif mode == 14:
            q, r = divmod(maximum - rng.randrange(1000000), 1000000)
            category, text = 'near_uint256', f'{q}.{r:06d}'
        else:
            q, r = divmod(rng.randrange(1000000), 1000000)
            category, text = 'subunit', f'{q}.{r:06d}'
        yield {'id': index, 'category': category, 'input': text}


# Hand-selected expectations are explicit fixtures, never derived by either parser.
EDGE_FIXTURES = [
    ('0', 0, 'Zero'),
    ('1', 1000000, 'Integer'),
    ('0.000001', 1, 'Minimum positive amount'),
    ('0.999999', 999999, 'Below one token'),
    ('12.3456', 12345600, 'Four decimal places'),
    ('1.000000', 1000000, 'Six trailing zeros allowed'),
    ('0.010000', 10000, 'Trailing zeros preserve exactness'),
    ('0.0', 0, 'Noncanonical zero is exact'),
    ('1.230000', 1230000, 'Canonical display removes zeros'),
    ('115792089237316195423570985008687907853269984665640564039457584007913129.639935',
     115792089237316195423570985008687907853269984665640564039457584007913129639935, 'uint256 maximum'),
    ('115792089237316195423570985008687907853269984665640564039457584007913129.639934',
     115792089237316195423570985008687907853269984665640564039457584007913129639934, 'One unit below maximum'),
    ('115792089237316195423570985008687907853269984665640564039457584007913129.639936', None, 'One unit above maximum'),
    ('115792089237316195423570985008687907853269984665640564039457584007913130', None, 'Whole amount over maximum'),
    ('', None, 'Empty'), ('00', None, 'Leading zero'), ('01', None, 'Leading zero'),
    ('00.1', None, 'Fraction does not excuse leading zero'),
    ('+1', None, 'Plus sign'), ('-1', None, 'Minus sign'), ('-0', None, 'Signed zero'),
    (' 1', None, 'Leading space'), ('1 ', None, 'Trailing space'),
    ('\t1', None, 'Tab'), ('1\n', None, 'Trailing LF'), ('1\r\n', None, 'Trailing CRLF'),
    ('.1', None, 'Missing whole digits'), ('1.', None, 'Missing fractional digits'),
    ('1..2', None, 'Repeated dot'), ('1e3', None, 'Exponent'), ('1E-6', None, 'Exponent'),
    ('0.0000001', None, 'Excess nonzero precision'), ('1.0000000', None, 'Excess zero precision'),
    ('١', None, 'Arabic-Indic digit'), ('１', None, 'Fullwidth digit'),
    ('𝟙', None, 'Mathematical digit'), ('1．0', None, 'Fullwidth dot'),
    ('1\u00a0', None, 'Nonbreaking space'), ('1\u200b', None, 'Zero-width space'),
    ('1_000', None, 'Underscore'), ('1,000', None, 'Thousands separator'),
    ('0x10', None, 'Hexadecimal'), ('NaN', None, 'NaN'), ('Infinity', None, 'Infinity'),
    ('1\x00', None, 'NUL'), ('9' * 80, None, 'Overlength'),
    ('1' * 1000, None, 'Huge malformed input'),
]


def decision(parser, text):
    """Normalize only expected user-input errors; internal errors propagate."""
    try:
        return {'accepted': True, 'units': parser(text)}
    except (ValueError, TypeError) as error:
        return {'accepted': False, 'error': type(error).__name__}


def evaluate(row):
    """Cross-check decisions, values and canonical round trips for one case."""
    actual = decision(parse, row['input'])
    oracle = decision(parse_reference, row['input'])
    result = dict(row, **actual, reference=oracle, oracle_match=actual == oracle)
    if actual['accepted']:
        canonical = format_units(actual['units'])
        result['canonical'] = canonical
        result['roundtrip_ok'] = (parse(canonical) == actual['units']
                                  and parse_reference(canonical) == actual['units']
                                  and format_units(parse(canonical)) == canonical)
    return result


def float_counterexamples():
    """Actually execute binary-float conversion, scaling, truncation and rounding."""
    examples = []
    for text in ['1.000001', '9007199254.740993', '99999999999.999999', '0.000249']:
        exact = parse(text)
        converted = float(text)
        scaled = converted * 1000000
        truncated = int(scaled)
        rounded = round(scaled)
        if truncated == exact:
            raise AssertionError('candidate is not a float counterexample')
        examples.append({'input': text, 'exact_units': exact,
                         'float_hex': converted.hex(), 'scaled_float_hex': scaled.hex(),
                         'scaled_float_repr': repr(scaled),
                         'float_truncated_units': truncated,
                         'truncation_error_units': truncated - exact,
                         'float_rounded_units': rounded,
                         'rounding_error_units': rounded - exact})
    return examples


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def publish(output, seed=SEED, count=CASE_COUNT):
    """Publish actual cases and deterministic results, raising on any discrepancy.

    Lower counts are allowed for fast unit tests. The submission/replay uses 100000.
    No timestamps or elapsed times are placed in reproducible artifacts.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    accepted = rejected = mismatches = roundtrip_failures = 0
    categories = Counter()
    distinct_inputs = set()
    digest = hashlib.sha256()
    with (output / 'generated_cases.jsonl').open('wb') as stream:
        for row in generated_cases(seed, count):
            result = evaluate(row)
            categories[row['category']] += 1
            distinct_inputs.add(row['input'])
            accepted += int(result['accepted'])
            rejected += int(not result['accepted'])
            mismatches += int(not result['oracle_match'])
            roundtrip_failures += int(result.get('roundtrip_ok') is False)
            encoded = (json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
            stream.write(encoded)
            digest.update(encoded)
    edges = []
    edge_failures = 0
    for index, (text, expected_units, reason) in enumerate(EDGE_FIXTURES):
        row = evaluate({'id': index, 'input': text, 'reason': reason})
        row['expected_accepted'] = expected_units is not None
        if expected_units is not None:
            row['expected_units'] = expected_units
        row['expected_match'] = (row['accepted'] == row['expected_accepted']
                                 and row.get('units') == expected_units)
        edge_failures += int(not row['expected_match'] or not row['oracle_match']
                             or row.get('roundtrip_ok') is False)
        edges.append(row)
    write_json(output / 'edge_cases.json', edges)
    table = ['# Hand-selected edge cases', '',
             'Expected decisions and units were written as fixtures before evaluation.', '',
             '| Input | Expected | Actual | Units / canonical | Reason |',
             '| --- | --- | --- | --- | --- |']
    for row in edges:
        escaped = json.dumps(row['input'], ensure_ascii=True).replace('|', '\\|')
        details = str(row['units']) + ' / ' + row['canonical'] if row['accepted'] else '—'
        table.append(f"| `{escaped}` | {'accept' if row['expected_accepted'] else 'reject'} | {'accept' if row['accepted'] else 'reject'} | {details} | {row['reason']} |")
    (output / 'edge_cases.md').write_text('\n'.join(table) + '\n', encoding='utf-8')
    report = {'schema_version': 1, 'seed': seed, 'generated_count': count,
              'accepted': accepted, 'rejected': rejected,
              'distinct_generated_inputs': len(distinct_inputs),
              'category_counts': dict(sorted(categories.items())),
              'oracle_comparisons': accepted + rejected, 'oracle_mismatches': mismatches,
              'roundtrip_checks': accepted, 'roundtrip_failures': roundtrip_failures,
              'edge_count': len(edges), 'edge_failures': edge_failures,
              'edge_oracle_comparisons': len(edges),
              'edge_roundtrip_checks': sum(row['accepted'] for row in edges),
              'cases_sha256': digest.hexdigest(),
              'float_counterexamples': float_counterexamples(),
              'runtime': {'implementation': sys.implementation.name,
                          'python': sys.version.split()[0],
                          'float_radix': sys.float_info.radix,
                          'float_mantissa_bits': sys.float_info.mant_dig},
              'status': 'PASS' if not (mismatches or roundtrip_failures or edge_failures) else 'FAIL'}
    write_json(output / 'report.json', report)
    if report['status'] != 'PASS':
        raise AssertionError('evidence mismatch; inspect report.json')
    return report
