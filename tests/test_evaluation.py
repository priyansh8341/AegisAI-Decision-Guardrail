"""Evaluation accounting checks; no Ollama, network or application database."""
import contextlib
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import load_cases, quote_counts, report, run_cases


class EvaluationTests(unittest.TestCase):
    def test_validation_diagnostics_survive_failure_accounting(self):
        class InvalidOutput(Exception):
            code = 'invalid_output'
            validation_issues = [{'path': ['assumptions', 0, 'verification'], 'type': 'missing'}]
        def fail(brief):
            raise InvalidOutput('Invalid model output')
        cases = [dict(id='diagnostic', split='development', kind='normal', brief={})]
        with contextlib.redirect_stdout(io.StringIO()):
            rows = run_cases(cases, fail)
        self.assertEqual(rows[0]['validation_issues'], InvalidOutput.validation_issues)
        self.assertEqual(report(rows, 1)['failed'], 1)

    def test_dataset_split_and_coverage(self):
        cases = load_cases(Path(__file__).resolve().parents[1]/'evaluation/cases.jsonl')
        self.assertEqual(len(cases), 30)
        self.assertEqual(sum(c['split'] == 'heldout' for c in cases), 10)
        for kind in ('normal', 'ambiguous', 'adversarial'):
            self.assertEqual(sum(c['kind'] == kind for c in cases), 10)

    def test_evidence_denominator_and_boundaries(self):
        brief = dict(decision='Use a shared login', constraints='For temporary staff')
        assessment = {'risks': [{'evidence': x} for x in ['SHARED   login', '', 'login For', 'invented']]}
        self.assertEqual(quote_counts(brief, assessment), dict(matched=1, unmatched=2, inferred=1))

    def test_failure_is_counted_and_offline_stops(self):
        class Offline(Exception):
            code = 'model_unavailable'
        def fail(brief):
            raise Offline('Offline')
        cases = [dict(id=str(i), split='development', kind='normal', brief={}) for i in range(3)]
        with contextlib.redirect_stdout(io.StringIO()):
            rows = run_cases(cases, fail)
        result = report(rows, 3)
        self.assertEqual((result['attempted'], result['unattempted'], result['valid']), (1, 2, 0))
        self.assertIsNone(result['quoted_evidence_match_rate'])

    def test_repeats_and_no_quote_is_not_perfect_grounding(self):
        cases = [dict(id='one', split='development', kind='normal', brief={})]
        with contextlib.redirect_stdout(io.StringIO()):
            rows = run_cases(cases, lambda b: {'risks': [{'evidence': ''}]}, 2)
        result = report(rows, 2)
        self.assertEqual(result['valid_rate'], 1)
        self.assertEqual(result['quote_counts']['inferred'], 2)
        self.assertIsNone(result['quoted_evidence_match_rate'])


if __name__ == '__main__':
    unittest.main()
