"""Offline dataset checks and live evaluations; never writes the application DB."""
import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_cases(path):
    cases = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    ids = set()
    for case in cases:
        if case['id'] in ids:
            raise ValueError('Duplicate case ID: ' + case['id'])
        ids.add(case['id'])
        if case['split'] not in ('development', 'heldout'):
            raise ValueError('Invalid split')
        if len(case['brief']['decision']) < 30 or not case['review_focus']:
            raise ValueError('Invalid case: ' + case['id'])
    if not cases:
        raise ValueError('Dataset is empty')
    return cases


def quote_counts(brief, assessment):
    # Deliberately independent of application scoring; no matches across field boundaries.
    sources = [' '.join(brief.get(k, '').split()).casefold() for k in ('decision', 'constraints')]
    counts = dict(matched=0, unmatched=0, inferred=0)
    for risk in assessment['risks']:
        quote = ' '.join(risk['evidence'].split()).casefold()
        key = 'inferred' if not quote else 'matched' if any(quote in source for source in sources) else 'unmatched'
        counts[key] += 1
    return counts


def run_cases(cases, assessor, repeats=1, on_result=None):
    rows = []
    for case in cases:
        for repeat in range(1, repeats + 1):
            start = time.perf_counter()
            row = dict(case_id=case['id'], split=case['split'], kind=case['kind'], repeat=repeat)
            try:
                assessment = assessor(case['brief'])
                row.update(status='valid', assessment=assessment, evidence=quote_counts(case['brief'], assessment))
            except Exception as exc:
                # Unexpected errors remain distinguishable from known model/validation failures.
                row.update(status='failed', error_code=getattr(exc, 'code', 'runner_error'), error=str(exc))
                if getattr(exc, 'validation_issues', None):
                    row['validation_issues'] = exc.validation_issues
            row['elapsed_seconds'] = round(time.perf_counter() - start, 4)
            rows.append(row)
            if on_result:
                on_result(row)
            print(f"{case['id']} repeat {repeat}: {row['status']}", flush=True)
            if row.get('error_code') == 'model_unavailable':
                return rows  # Fail fast; remaining cases are explicitly counted as unattempted.
    return rows


def report(rows, planned):
    valid = [r for r in rows if r['status'] == 'valid']
    totals = {key: sum(r['evidence'][key] for r in valid) for key in ('matched', 'unmatched', 'inferred')}
    times = sorted(r['elapsed_seconds'] for r in rows)
    quoted = totals['matched'] + totals['unmatched']
    return dict(planned=planned, attempted=len(rows), unattempted=planned-len(rows), valid=len(valid), failed=len(rows)-len(valid),
                valid_rate=len(valid)/len(rows) if rows else None,
                quote_counts=totals, quoted_evidence_match_rate=totals['matched']/quoted if quoted else None,
                median_attempt_seconds=statistics.median(times) if times else None,
                p95_attempt_seconds=times[math.ceil(.95*len(times))-1] if times else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT/'evaluation/cases.jsonl')
    parser.add_argument('--split', choices=['development', 'heldout', 'all'], default='development')
    parser.add_argument('--check', action='store_true', help='Check dataset only; no dependencies or model calls')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--consistency-check', action='store_true', help='Include the second-pass review used by the app')
    parser.add_argument('--output', type=Path, default=ROOT/'evaluation/runs')
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    cases = load_cases(args.dataset)
    cases = [c for c in cases if args.split == 'all' or c['split'] == args.split]
    if not cases:
        parser.error('No cases in selected split')
    if args.check:
        print(f'Dataset valid: {len(cases)} cases; split={args.split}. No model calls made.')
        return 0
    try:
        import agent
        from models import Brief, LiveAssessment
    except ImportError as exc:
        parser.error(f'Install requirements.txt first: {exc}')
    # Validate every selected input before spending model time.
    for case in cases:
        Brief.model_validate(case['brief'])
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination = args.output/run_id
    destination.mkdir(parents=True, exist_ok=False)
    metadata = dict(created_utc=run_id, model=agent.MODEL, ollama_url=agent.OLLAMA_URL,
                    prompt_version=agent.PROMPT_VERSION, python=sys.version, platform=platform.platform(),
                    split=args.split, repeats=args.repeats,
                    consistency_check=args.consistency_check,
                    dataset_sha256=hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
                    agent_sha256=hashlib.sha256((ROOT/'agent.py').read_bytes()).hexdigest(),
                    models_sha256=hashlib.sha256((ROOT/'models.py').read_bytes()).hexdigest(),
                    note='Synthetic benchmark; cold-start included; quality requires human review. No token/cost measurement.')
    (destination/'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    (destination/'generation_schema.json').write_text(json.dumps(LiveAssessment.model_json_schema(), indent=2), encoding='utf-8')
    (destination/'cases.json').write_text(json.dumps(cases, indent=2), encoding='utf-8')
    rows = []
    interrupted = False
    def assessor(brief):
        value = Brief.model_validate(brief)
        assessment = agent.assess_decision(value)
        result = assessment.model_dump()
        if args.consistency_check:
            import quality
            result['quality_review'] = quality.review_assessment(value, assessment)
        return result
    def checkpoint(row):
        rows.append(row)
        with (destination/'results.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(row)+'\n')
    try:
        run_cases(cases, assessor, args.repeats, checkpoint)
    except KeyboardInterrupt:
        interrupted = True
    (destination/'results.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows), encoding='utf-8')
    summary = report(rows, len(cases)*args.repeats)
    summary['interrupted'] = interrupted
    if args.consistency_check:
        from collections import Counter
        summary['quality_review_statuses'] = dict(Counter(r.get('assessment', {}).get('quality_review', {}).get('status', 'not_run') for r in rows))
    (destination/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    with (destination/'human_review.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['case_id', 'repeat', 'reviewer', 'risk_relevance_0_2', 'grounding_0_2',
                         'actionability_0_2', 'uncertainty_0_2', 'instruction_resistance_0_2_or_NA', 'notes'])
        for row in rows:
            if row['status'] == 'valid':
                writer.writerow([row['case_id'], row['repeat']] + ['']*8)
    lines = ['# AegisAI evaluation run', '', '```json', json.dumps(summary, indent=2), '```', '',
             'Schema validity is not answer accuracy. Quote matches verify text presence only.',
             'Blank human-review scores are unreviewed, never zero. See ../../README.md for the rubric.',
             'Failures are included in attempt latency; report valid-only latency separately if needed.',
             'Synthetic scenarios do not establish real-world risk prediction or business impact.']
    (destination/'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    print('Saved evaluation:', destination)
    return 0 if summary['valid'] == summary['planned'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
