"""Transparent prioritisation, not a probability or compliance certification."""
from models import Brief, ModelAssessment

POLICY_VERSION = 'risk-matrix-1.0'
THRESHOLDS = {'Cautious': 32, 'Balanced': 48, 'Flexible': 64}

def grade(score):
    return 'CRITICAL' if score >= 80 else 'HIGH' if score >= 60 else 'MEDIUM' if score >= 32 else 'LOW'

def enrich(brief: Brief, assessment: ModelAssessment):
    source = ' '.join((brief.decision + ' ' + brief.constraints).split()).casefold()
    risks = []
    for i, risk in enumerate(assessment.risks, 1):
        item = risk.model_dump()
        quote = ' '.join(risk.evidence.split()).casefold()
        item.update(id=f'R{i:02}', score=risk.likelihood * risk.impact * 4)
        item['level'] = grade(item['score'])
        item['evidence_status'] = 'matched' if quote and quote in source else 'unverified' if quote else 'inferred'
        risks.append(item)
    risks.sort(key=lambda x: x['score'], reverse=True)
    score = max(r['score'] for r in risks)
    threshold = THRESHOLDS[brief.appetite]
    recommendation = 'BLOCK' if score >= 80 else 'REVISE' if score >= threshold else 'REVIEW'
    return {
        **assessment.model_dump(exclude={'risks'}), 'risks': risks, 'score': score,
        'level': grade(score), 'recommendation': recommendation,
        'policy_version': POLICY_VERSION, 'review_threshold': threshold,
        'evidence_matches': sum(r['evidence_status'] == 'matched' for r in risks),
        'policy_explanation': f'Highest risk: likelihood × impact × 4 = {score}/100. '
            f'{brief.appetite} review threshold: {threshold}. Scores of 80 or more trigger BLOCK. '
            'Every result requires a human decision. Scores are ordinal priorities, not probabilities.',
    }
