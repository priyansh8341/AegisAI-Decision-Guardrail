"""AegisAI v2: local decision review workspace. Run with uvicorn server:app."""
from contextlib import asynccontextmanager
from pathlib import Path
import json
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import agent
import quality
from models import Brief, AssessmentRequest, ReviewRequest
from policy import enrich
from samples import SAMPLES, get_sample
import store

ROOT = Path(__file__).parent

@asynccontextmanager
async def lifespan(app):
    store.init_db()
    yield

app = FastAPI(title='AegisAI Decision Workspace', version='2.1.0', lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')

@app.middleware('http')
async def local_protection(request: Request, call_next):
    # Prevent cross-origin browser writes to this unauthenticated local workspace.
    if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'error': {'message': 'Cross-origin requests are not allowed.'}}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    return response

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    messages = ['.'.join(str(p) for p in e['loc'][1:]) + ': ' + e['msg'] for e in exc.errors()]
    return JSONResponse({'error': {'code': 'invalid_input', 'message': '; '.join(messages)}}, status_code=422)

@app.get('/')
def home():
    return FileResponse(ROOT / 'static' / 'index.html')

@app.get('/health')
def health():
    return {'ok': True, 'version': '2.1.0'}

@app.get('/docs', include_in_schema=False)
def docs():
    return FileResponse(ROOT / 'static' / 'api.html')

@app.get('/api/status')
def status():
    return agent.model_status()

@app.get('/api/samples')
def samples():
    return [{'id': key, 'name': value['name'], 'brief': value['brief']} for key, value in SAMPLES.items()]

@app.post('/api/assess', status_code=201)
def assess(payload: AssessmentRequest):
    start = time.perf_counter()
    brief = Brief.model_validate(payload.model_dump(exclude={'mode', 'sample_id'}))
    error, result = None, None
    if payload.mode == 'sample':
        if payload.sample_id not in SAMPLES:
            raise HTTPException(422, 'Choose an available sample.')
        fixture_brief, model_result = get_sample(payload.sample_id)
        if fixture_brief != brief:
            raise HTTPException(422, 'Sample mode only runs the unedited sample brief. Switch to live mode to assess your own decision.')
        result = enrich(brief, model_result)
        engine = 'Fixed sample / ' + payload.sample_id
    else:
        engine = agent.MODEL + ' / ' + agent.PROMPT_VERSION
        try:
            assessment = agent.assess_decision(brief)
            result = enrich(brief, assessment)
            if quality.REVIEW_ENABLED:
                result['quality_review'] = quality.review_assessment(brief, assessment)
        except agent.AssessmentError as exc:
            error = {'code': exc.code, 'message': exc.message}
    record = store.save(brief.model_dump(), payload.mode, engine, result, error, round((time.perf_counter() - start) * 1000))
    return JSONResponse(record, status_code=201 if result else 502)

@app.get('/api/assessments')
def history():
    records, total = store.list_records()
    return {'records': records, 'total': total}

@app.get('/api/assessments/{record_id}')
def detail(record_id: str):
    record = store.get(record_id)
    if not record:
        raise HTTPException(404, 'Assessment not found.')
    return record

@app.post('/api/assessments/{record_id}/review')
def review(record_id: str, payload: ReviewRequest):
    state = store.review(record_id, payload)
    if state == 'missing':
        raise HTTPException(404, 'Assessment not found.')
    if state == 'failed':
        raise HTTPException(409, 'A failed assessment cannot be approved. Run a successful assessment first.')
    if state == 'conflict':
        raise HTTPException(409, 'This assessment was reviewed elsewhere. Reopen it before saving your review.')
    if state == 'checklist':
        raise HTTPException(422, 'Complete the human-review checklist before approving a live assessment.')
    return store.get(record_id)

def markdown(record):
    b, r = record['brief'], record['result']
    lines = ['# AegisAI decision report', '', '# ' + b['title'], '',
        f"Record: {record['id']} | Created: {record['created_at']}",
        f"Mode: {record['mode'].upper()} | Engine: {record['engine']}",
        f"Human review: {record['review_status']}", '', '## Decision', b['decision'], '',
        '## Constraints', b['constraints'] or 'Not supplied', '',
        f"Owner: {b['owner'] or 'Not assigned'} | Risk appetite: {b['appetite']}", '']
    if r:
        lines += ['## Assessment', r['executive_summary'], '',
            f"Risk priority: {r['score']}/100 ({r['level']}) | Policy signal: {r['recommendation']}",
            r['policy_explanation'], '', '## Risk register']
        if r.get('quality_review'):
            q = r['quality_review']
            lines += ['## Automated consistency review', q['status'], q['limitation']]
            if q.get('message'):
                lines += [q['message']]
            for finding in q['findings']:
                lines += [f"- {finding['severity'].upper()} | {finding['kind']} | {finding['field']}",
                          '> '+finding['quote'], finding['explanation']]
        for risk in r['risks']:
            lines += [f"### {risk['id']}: {risk['title']}", f"{risk['category']} | Likelihood {risk['likelihood']}/5 | Impact {risk['impact']}/5 | Priority {risk['score']}/100",
                risk['rationale'], 'Evidence (' + risk['evidence_status'] + '): ' + (risk['evidence'] or 'Inferred; no source quotation'),
                'Mitigation: ' + risk['mitigation'], 'Monitor: ' + risk['monitoring_signal'], '']
        for title, key in [('Assumptions', 'assumptions'), ('Open questions', 'open_questions'), ('Next steps', 'next_steps')]:
            lines += ['## ' + title] + ['- ' + v for v in r[key]] + ['']
        lines += ['## Scenario outlook'] + [f"{k.replace('_', ' ').title()}: {v}" for k, v in r['outlook'].items()]
    else:
        lines += ['## Assessment failed', record['error']['message'], 'No risk score was assigned.']
    lines += ['', '## Review history']
    for event in record['reviews']:
        lines += [f"- {event['created_at']} | {event['reviewer']} | {event['action']}", event['note']]
    lines += ['', '## Limitations', 'Local single-user decision-support prototype. Sample reports are fixed fixtures. '
        'Live assessments are generated by a model and may be wrong. Scores are uncalibrated ordinal priorities, '
        'not probabilities. Reviews record local user-entered names, not authenticated identities. '
        'Recommendations do not execute or enforce external actions.']
    return '\n'.join(lines)

@app.get('/api/assessments/{record_id}/export/{kind}')
def export(record_id: str, kind: str):
    record = detail(record_id)
    if kind not in {'json', 'md'}:
        raise HTTPException(404, 'Choose json or md.')
    body = json.dumps(record, indent=2, ensure_ascii=False) if kind == 'json' else markdown(record)
    return Response(body, media_type='application/json' if kind == 'json' else 'text/markdown',
        headers={'Content-Disposition': f'attachment; filename="aegis-{record_id}.{kind}"'})
