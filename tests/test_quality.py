import sys
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from samples import get_sample
from quality import ReviewOutput, validate_findings, review_assessment


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.brief, self.assessment = get_sample('migration')

    def test_invented_target_quote_is_rejected(self):
        review = ReviewOutput.model_validate({'findings':[dict(kind='unsupported_claim',severity='high',field='assumptions',quote='A fabricated claim never made.',source_quote='',explanation='This is a fabricated quotation in a reviewer response.')]})
        with self.assertRaises(ValueError):
            validate_findings(self.brief,self.assessment.model_dump(),review)

    def test_fabricated_source_quote_is_rejected(self):
        review = ReviewOutput.model_validate({'findings':[dict(kind='contradiction',severity='high',field='assumptions',quote=self.assessment.assumptions[0],source_quote='This quotation was invented.',explanation='The reviewer must not invent source context.')]})
        with self.assertRaises(ValueError):
            validate_findings(self.brief,self.assessment.model_dump(),review)

    def test_matching_quotes_do_not_claim_truth(self):
        review = ReviewOutput.model_validate({'findings':[dict(kind='weak_verification',severity='medium',field='assumptions',quote=self.assessment.assumptions[0],source_quote='',explanation='A concrete verification method is not included in this condition.')]})
        self.assertEqual(len(validate_findings(self.brief,self.assessment.model_dump(),review).findings),1)

    def test_offline_check_is_not_clean_result(self):
        with patch('quality.requests.post',side_effect=requests.ConnectionError()):
            result=review_assessment(self.brief,self.assessment)
        self.assertEqual(result['status'],'check_failed')
        self.assertIn('not a clean result',result['message'])

    def test_empty_findings_are_not_approval(self):
        response=Mock();response.json.return_value={'response':json.dumps({'findings':[]})}
        with patch('quality.requests.post',return_value=response):
            result=review_assessment(self.brief,self.assessment)
        self.assertEqual(result['status'],'no_issues_detected')
        self.assertIn('Human review',result['limitation'])

if __name__=='__main__':unittest.main()
