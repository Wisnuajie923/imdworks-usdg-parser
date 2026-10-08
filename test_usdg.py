"""Standard-library regression tests, developed in recorded vertical cycles."""
import importlib
import importlib.util
import unittest


class ParserTests(unittest.TestCase):
    def parser(self):
        self.assertIsNotNone(importlib.util.find_spec('usdg'), 'production parser is missing')
        return importlib.import_module('usdg')

    def test_exact_scaling(self):
        parse = self.parser().parse
        for text, units in [('0', 0), ('1', 1000000), ('0.000001', 1),
                            ('12.3456', 12345600), ('1.000000', 1000000),
                            ('0.010000', 10000)]:
            with self.subTest(text=text):
                self.assertEqual(parse(text), units)

    def test_ascii_strict_grammar(self):
        parse = self.parser().parse
        invalid = ['', '00', '01', '00.1', '+1', '-0', '-1', ' 1', '1 ',
                   '\t1', '1\n', '.1', '1.', '1..2', '1e3', '1E-6',
                   '1_000', '1,000', '١', '１', '𝟙', '1．0', '1\u00a0',
                   '0.0000000', '1.1234567', '0x10', 'NaN', 'Infinity',
                   '1\x00', '1/2', '1.٢', '1\r\n']
        for text in invalid:
            with self.subTest(text=repr(text)), self.assertRaises(ValueError):
                parse(text)

    def test_uint256_and_bounded_input(self):
        module = self.parser()
        maximum = (1 << 256) - 1
        whole, remainder = divmod(maximum, 1000000)
        self.assertEqual(module.parse(f'{whole}.{remainder:06d}'), maximum)
        self.assertEqual(module.parse(str(whole)), whole * 1000000)
        for text in [f'{whole}.{remainder + 1:06d}', str(whole + 1),
                     '9' * 79, '1' * 1000000, '0.' + '0' * 1000000,
                     'x' * 1000000]:
            with self.subTest(length=len(text)), self.assertRaises(ValueError):
                module.parse(text)
        for value in [True, False, None, 1, 1.0, b'1', [], {}, object()]:
            with self.subTest(type=type(value).__name__), self.assertRaises(TypeError):
                module.parse(value)
        self.assertTrue(hasattr(module, 'MAX_INPUT_LENGTH'), 'length guard is missing')
        self.assertEqual(module.MAX_INPUT_LENGTH, 79)
        self.assertEqual(module.UINT256_MAX, maximum)

    def test_canonical_formatter_and_integer_roundtrip(self):
        module = self.parser()
        self.assertTrue(hasattr(module, 'format_units'), 'formatter is missing')
        fmt = module.format_units
        pairs = [(0, '0'), (1, '0.000001'), (10, '0.00001'),
                 (1000000, '1'), (12345600, '12.3456'),
                 ((1 << 256) - 1,
                  '115792089237316195423570985008687907853269984665640564039457584007913129.639935')]
        for units, text in pairs:
            self.assertEqual(fmt(units), text)
            self.assertEqual(module.parse(fmt(units)), units)
        for units in [True, False, None, '1', 1.0, b'1', [], {}]:
            with self.subTest(type=type(units).__name__), self.assertRaises(TypeError):
                fmt(units)
        for units in [-1, 1 << 256, 1 << 100000]:
            with self.assertRaises(ValueError):
                fmt(units)
        for units in range(10001):
            self.assertEqual(module.parse(fmt(units)), units)

    def test_independent_character_oracle(self):
        self.assertIsNotNone(importlib.util.find_spec('reference'), 'reference parser is missing')
        ref = importlib.import_module('reference').parse_reference
        for text, units in [('0', 0), ('123.000010', 123000010),
                            ('0.1', 100000), ('0.000001', 1),
                            ('115792089237316195423570985008687907853269984665640564039457584007913129.639935', (1 << 256) - 1)]:
            self.assertEqual(ref(text), units)
        for text in ['', '01', '00.1', '1.', '.1', '1..2', '1.1234567',
                     '١', '１', '+1', '1\n', '1e2', '1_0',
                     '115792089237316195423570985008687907853269984665640564039457584007913129.639936',
                     '9' * 1000000]:
            with self.subTest(text=text[:80]), self.assertRaises(ValueError):
                ref(text)
        for value in [True, None, 1, 1.0, b'1']:
            with self.assertRaises(TypeError):
                ref(value)

    def runner(self):
        self.assertIsNotNone(importlib.util.find_spec('evidence'), 'seeded evidence runner is missing')
        return importlib.import_module('evidence')

    def test_seeded_generator(self):
        module = self.runner()
        first = list(module.generated_cases(917203, 1000))
        self.assertEqual(first, list(module.generated_cases(917203, 1000)))
        self.assertNotEqual(first, list(module.generated_cases(917204, 1000)))
        self.assertEqual(len(first), 1000)
        categories = {row['category'] for row in first}
        self.assertGreaterEqual(len(categories), 10)
        accepted = rejected = 0
        ref = importlib.import_module('reference').parse_reference
        for row in first:
            try:
                expected = ref(row['input'])
            except ValueError:
                rejected += 1
                continue
            accepted += 1
            self.assertEqual(self.parser().parse(row['input']), expected)
        self.assertGreater(accepted, 100)
        self.assertGreater(rejected, 100)

    def test_published_evidence(self):
        import hashlib
        import json
        import tempfile
        from pathlib import Path
        module = self.runner()
        self.assertTrue(hasattr(module, 'publish'), 'evidence publisher is missing')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            output = Path(directory)
            report = module.publish(output, seed=917203, count=1600)
            self.assertEqual(report['generated_count'], 1600)
            self.assertEqual(report['accepted'] + report['rejected'], 1600)
            self.assertEqual(report['oracle_comparisons'], 1600)
            self.assertEqual(report['oracle_mismatches'], 0)
            self.assertEqual(report['roundtrip_checks'], report['accepted'])
            self.assertEqual(report['roundtrip_failures'], 0)
            self.assertGreaterEqual(report['edge_count'], 30)
            self.assertEqual(report['edge_failures'], 0)
            self.assertEqual(report['status'], 'PASS')
            rows = [json.loads(line) for line in (output / 'generated_cases.jsonl').read_text().splitlines()]
            self.assertEqual(len(rows), 1600)
            self.assertEqual(sum(row['accepted'] for row in rows), report['accepted'])
            self.assertEqual(report['cases_sha256'], hashlib.sha256((output / 'generated_cases.jsonl').read_bytes()).hexdigest())
            edges = json.loads((output / 'edge_cases.json').read_text())
            self.assertEqual(len(edges), report['edge_count'])
            self.assertTrue(all(row['expected_accepted'] == row['accepted'] for row in edges))
            self.assertTrue(all(row.get('expected_units') == row.get('units') for row in edges))
            self.assertIn('| Input |', (output / 'edge_cases.md').read_text())
            examples = report['float_counterexamples']
            self.assertGreaterEqual(len(examples), 3)
            for row in examples:
                exact = self.parser().parse(row['input'])
                self.assertEqual(exact, row['exact_units'])
                self.assertEqual(int(float(row['input']) * 1000000), row['float_truncated_units'])
                self.assertNotEqual(exact, row['float_truncated_units'])
                self.assertEqual(round(float(row['input']) * 1000000), row['float_rounded_units'])
            prior = (output / 'generated_cases.jsonl').read_bytes()
            self.assertEqual(module.publish(output, seed=917203, count=1600), report)
            self.assertEqual((output / 'generated_cases.jsonl').read_bytes(), prior)

    def test_one_command_replay_entrypoint(self):
        self.assertIsNotNone(importlib.util.find_spec('run_tests'), 'one-command replay is missing')
        module = importlib.import_module('run_tests')
        self.assertTrue(callable(module.main))


if __name__ == '__main__':
    unittest.main()
