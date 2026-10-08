#!/usr/bin/env python3
"""One-command replay: regression suite, 100000 actual cases and read-back checks."""
import hashlib
import json
from pathlib import Path
import unittest

from evidence import CASE_COUNT, SEED, evaluate, publish


def main():
    root = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(str(root), pattern='test_usdg.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    output = root / 'results'
    report = publish(output, seed=SEED, count=CASE_COUNT)
    # Validate the bytes actually published, not just the in-memory counters.
    digest = hashlib.sha256()
    count = accepted = 0
    with (output / 'generated_cases.jsonl').open('rb') as stream:
        for line in stream:
            digest.update(line)
            row = json.loads(line)
            if row['id'] != count:
                raise AssertionError('published IDs are not contiguous')
            recomputed = evaluate({key: row[key] for key in ('id', 'category', 'input')})
            if row != recomputed:
                raise AssertionError(f'published case differs: {count}')
            accepted += int(row['accepted'])
            count += 1
    if (count != CASE_COUNT or accepted != report['accepted']
            or digest.hexdigest() != report['cases_sha256']):
        raise AssertionError('published dataset totals or hash differ')
    saved_report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
    if saved_report != report:
        raise AssertionError('published report differs')
    print(f"PASS: {result.testsRun} tests; {count} published/read-back cases; "
          f"{report['accepted']} accepted; {report['rejected']} rejected; "
          f"{report['edge_count']} edges; {len(report['float_counterexamples'])} float counterexamples")
    print(f"Seed: {SEED}; oracle mismatches: {report['oracle_mismatches']}; "
          f"roundtrip failures: {report['roundtrip_failures']}")
    print(f"Dataset SHA256: {report['cases_sha256']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
