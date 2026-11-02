"""Behaviour checks with simulated models and an isolated on-disk database."""
import copy
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import requests
from fastapi.testclient import TestClient
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent
from models import AssessmentRequest, ModelAssessment
from policy import enrich
from samples import SAMPLES, get_sample
import server
import store

class AppTests(unittest.TestCase):
    def setUp(self):
        self.quality_patch = patch.object(server.quality, 'review_assessment', return_value={
            'status': 'no_issues_detected', 'findings': [], 'limitation': 'Simulated check; human review required.'})
        self.quality_mock = self.quality_patch.start()
        self.addCleanup(self.quality_patch.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = store.DB_PATH
        store.DB_PATH = Path(self.temp.name) / 'test.db'
        self.client = TestClient(server.app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        store.DB_PATH = self.old_db
        self.temp.cleanup()

    def payload(self, sample='migration', mode='sample'):
        return {**SAMPLES[sample]['brief'], 'mode': mode, 'sample_id': sample}

    def create(self, sample='migration'):
        response = self.client.post('/api/assess', json=self.payload(sample))
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_sample_policy_and_provenance(self):
        record = self.create()
        self.assertEqual(record['result']['score'], 80)
        self.assertEqual(record['result']['recommendation'], 'BLOCK')
        self.assertEqual(record['mode'], 'sample')
        self.assertEqual(record['result']['evidence_matches'], 2)
        self.assertIn('sample', record['engine'])

    def test_lower_priority_sample_still_requires_review(self):
        record = self.create('docs')
        self.assertEqual(record['result']['score'], 24)
        self.assertEqual(record['result']['recommendation'], 'REVIEW')
        self.assertEqual(record['review_status'], 'PENDING')

    def test_sample_cannot_assess_edited_content(self):
        payload = self.payload()
        payload['decision'] += ' Edited content.'
        self.assertEqual(self.client.post('/api/assess', json=payload).status_code, 422)
        self.assertEqual(self.client.get('/api/assessments').json()['total'], 0)

    def test_invalid_or_blank_brief_rejected_before_generation(self):
        payload = self.payload(mode='live')
        payload['decision'] = ' ' * 50
        with patch.object(agent, 'assess_decision') as model:
            response = self.client.post('/api/assess', json=payload)
        self.assertEqual(response.status_code, 422)
        model.assert_not_called()

    def test_schema_rejects_wrong_ratings_and_missing_fields(self):
        for invalid in [0, 6, 999, True, '3', 2.5]:
            payload = copy.deepcopy(SAMPLES['migration']['assessment'])
            payload['risks'][0]['likelihood'] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                ModelAssessment.model_validate(payload)
        payload = copy.deepcopy(SAMPLES['migration']['assessment'])
        payload['confidence'] = .9
        with self.assertRaises(ValidationError):
            ModelAssessment.model_validate(payload)

    def test_model_malformed_output_has_no_fabricated_score(self):
        response = Mock()
        response.json.return_value = {'response': 'This is not JSON.'}
        with patch.object(agent.requests, 'post', return_value=response):
            attempt = self.client.post('/api/assess', json=self.payload(mode='live'))
        self.assertEqual(attempt.status_code, 502)
        record = attempt.json()
        self.assertIsNone(record['result'])
        self.assertEqual(record['error']['code'], 'invalid_output')
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(record['review_status'], 'NOT_APPLICABLE')
        self.assertEqual(self.client.get('/api/assessments').json()['total'], 1)

    def test_connection_and_timeout_failures_are_saved(self):
        for failure, code in [(requests.ConnectionError(), 'model_unavailable'), (requests.Timeout(), 'model_timeout')]:
            with self.subTest(code=code), patch.object(agent.requests, 'post', side_effect=failure):
                response = self.client.post('/api/assess', json=self.payload(mode='live'))
                self.assertEqual(response.status_code, 502)
                self.assertEqual(response.json()['error']['code'], code)
                self.assertIsNone(response.json()['result'])

    def test_valid_live_response_constrained_and_labelled(self):
        response = Mock()
        generated = copy.deepcopy(SAMPLES['launch']['assessment'])
        generated['assumptions'] = [{'condition': 'Before proceeding, the feature flag must disable the portal safely.',
                                     'verification': 'Test disabling the portal in the staging environment.'}]
        response.json.return_value = {'response': json.dumps(generated)}
        with patch.object(agent.requests, 'post', return_value=response) as call:
            result = self.client.post('/api/assess', json=self.payload('launch', mode='live'))
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.json()['mode'], 'live')
        self.assertEqual(result.json()['result']['score'], 60)
        self.assertIn('properties', call.call_args.kwargs['json']['format'])
        self.assertFalse(call.call_args.kwargs['json']['stream'])
        self.assertNotIn('quality_review', result.json()['result'])

    def test_quality_warning_survives_save_and_exports(self):
        self.enabled_patch = patch.object(server.quality, 'REVIEW_ENABLED', True)
        self.enabled_patch.start()
        self.addCleanup(self.enabled_patch.stop)
        self.quality_mock.return_value = {'status': 'issues_found', 'limitation': 'Human review required.',
            'findings': [{'severity': 'high', 'kind': 'contradiction', 'field': 'assumptions',
                          'quote': 'Unverified example condition', 'source_quote': '',
                          'explanation': 'The condition conflicts with the proposed constraints.'}]}
        generated = copy.deepcopy(SAMPLES['launch']['assessment'])
        generated['assumptions'] = [{'condition': 'Obtain a tested rollback before release.',
                                    'verification': 'Run the rollback procedure in staging and confirm access.'}]
        response = Mock()
        response.json.return_value = {'response': json.dumps(generated)}
        with patch.object(agent.requests, 'post', return_value=response):
            record = self.client.post('/api/assess', json=self.payload('launch', mode='live')).json()
        saved = self.client.get('/api/assessments/'+record['id']).json()
        self.assertEqual(saved['result']['quality_review']['status'], 'issues_found')
        text = self.client.get('/api/assessments/'+record['id']+'/export/md').text
        self.assertIn('Automated consistency review', text)
        self.assertIn('The condition conflicts', text)

    def test_live_approval_requires_all_human_checks_and_records_acknowledgement(self):
        brief, assessment = get_sample('launch')
        record = store.save(brief.model_dump(), 'live', 'Simulated test model', enrich(brief, assessment), None, 1)
        path = '/api/assessments/'+record['id']+'/review'
        request = dict(action='APPROVED', reviewer='Test reviewer', note='Reviewed the supplied brief and practical mitigations.', expected_version=0)
        self.assertEqual(self.client.post(path,json=request).status_code,422)
        request['checks_completed']=['source_facts','source_facts','actionability']
        self.assertEqual(self.client.post(path,json=request).status_code,422)
        self.assertEqual(store.get(record['id'])['version'],0)
        request['checks_completed']=['source_facts','contradictions','actionability']
        approved=self.client.post(path,json=request)
        self.assertEqual(approved.status_code,200)
        self.assertIn('Human checklist acknowledged',approved.json()['reviews'][0]['note'])

    def test_live_revision_does_not_require_approval_checklist(self):
        brief, assessment = get_sample('launch')
        record=store.save(brief.model_dump(),'live','Simulated test model',enrich(brief,assessment),None,1)
        response=self.client.post('/api/assessments/'+record['id']+'/review',json=dict(
            action='REVISION_REQUESTED',reviewer='Test reviewer',note='Resolve contradictory assumptions before using the report.',expected_version=0))
        self.assertEqual(response.status_code,200)

    def test_evidence_presence_does_not_silently_verify_inventions(self):
        brief, assessment = get_sample('migration')
        assessment.risks[0].evidence = 'A fabricated source quotation'
        result = enrich(brief, assessment)
        self.assertEqual(result['risks'][0]['evidence_status'], 'unverified')
        self.assertEqual(result['evidence_matches'], 1)

    def test_review_is_durable_append_only_and_conflict_checked(self):
        record = self.create()
        path = '/api/assessments/' + record['id'] + '/review'
        request = dict(action='REVISION_REQUESTED', reviewer='Test reviewer', note='Retain and test the rollback environment.', expected_version=0)
        response = self.client.post(path, json=request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['version'], 1)
        self.assertEqual(self.client.post(path, json=request).status_code, 409)
        request.update(action='APPROVED', note='Conditions were reviewed in this synthetic test.', expected_version=1)
        self.assertEqual(self.client.post(path, json=request).status_code, 200)
        store.init_db()  # Opening/initialising a new database connection preserves records.
        persisted = self.client.get('/api/assessments/' + record['id']).json()
        self.assertEqual(len(persisted['reviews']), 2)
        self.assertEqual(persisted['review_status'], 'APPROVED')

    def test_failed_assessment_cannot_be_reviewed(self):
        with patch.object(agent.requests, 'post', side_effect=requests.ConnectionError()):
            record = self.client.post('/api/assess', json=self.payload(mode='live')).json()
        response = self.client.post('/api/assessments/' + record['id'] + '/review', json=dict(
            action='APPROVED', reviewer='Test reviewer', note='This must be rejected.', expected_version=0))
        self.assertEqual(response.status_code, 409)

    def test_export_includes_provenance_and_review(self):
        record = self.create()
        path = '/api/assessments/' + record['id']
        self.client.post(path + '/review', json=dict(action='BLOCKED', reviewer='Test reviewer', note='Rollback must be established first.', expected_version=0))
        md = self.client.get(path + '/export/md')
        self.assertEqual(md.status_code, 200)
        self.assertIn('Mode: SAMPLE', md.text)
        self.assertIn('Rollback must be established first.', md.text)
        exported = self.client.get(path + '/export/json').json()
        self.assertEqual(exported['reviews'][0]['action'], 'BLOCKED')
        self.assertEqual(self.client.get(path + '/export/html').status_code, 404)

    def test_cross_origin_browser_writes_rejected(self):
        response = self.client.post('/api/assess', json=self.payload(), headers={'Origin': 'https://untrusted.example'})
        self.assertEqual(response.status_code, 403)

    def test_review_requires_reason_and_reviewer(self):
        record = self.create()
        response = self.client.post('/api/assessments/' + record['id'] + '/review', json=dict(action='APPROVED', reviewer='', note='', expected_version=0))
        self.assertEqual(response.status_code, 422)

    def test_missing_record_and_health(self):
        self.assertEqual(self.client.get('/api/assessments/missing').status_code, 404)
        self.assertEqual(self.client.get('/health').json()['version'], '2.1.0')
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/docs').status_code, 200)
        self.assertIn('nosniff', self.client.get('/').headers['X-Content-Type-Options'])

if __name__ == '__main__':
    unittest.main()
