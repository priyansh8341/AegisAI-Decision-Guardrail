"""SQLite persistence. Each human review is appended to an audit log."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import sqlite3
import uuid

DB_PATH = Path(os.getenv('AEGIS_DB', str(Path(__file__).parent / 'data' / 'aegis.db')))

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS assessments (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL, brief TEXT NOT NULL,
            mode TEXT NOT NULL, engine TEXT NOT NULL, status TEXT NOT NULL,
            result TEXT, error TEXT, review_status TEXT NOT NULL DEFAULT 'PENDING',
            version INTEGER NOT NULL DEFAULT 0, duration_ms INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT NOT NULL REFERENCES assessments(id),
            created_at TEXT NOT NULL, reviewer TEXT NOT NULL, action TEXT NOT NULL, note TEXT NOT NULL
        );
        ''')

def save(brief, mode, engine, result, error, duration_ms):
    record_id = uuid.uuid4().hex[:12]
    with connect() as db:
        db.execute('INSERT INTO assessments(id,created_at,brief,mode,engine,status,result,error,duration_ms,review_status) VALUES(?,?,?,?,?,?,?,?,?,?)',
            (record_id, now(), json.dumps(brief), mode, engine, 'completed' if result else 'failed',
             json.dumps(result) if result else None, json.dumps(error) if error else None, duration_ms, 'PENDING' if result else 'NOT_APPLICABLE'))
    return get(record_id)

def unpack(row):
    if row is None:
        return None
    result = dict(row)
    for key in ['brief', 'result', 'error']:
        result[key] = json.loads(result[key]) if result[key] else None
    return result

def get(record_id):
    with connect() as db:
        record = unpack(db.execute('SELECT * FROM assessments WHERE id=?', (record_id,)).fetchone())
        if record:
            record['reviews'] = [dict(r) for r in db.execute('SELECT created_at,reviewer,action,note FROM reviews WHERE assessment_id=? ORDER BY id DESC', (record_id,))]
    return record

def list_records():
    with connect() as db:
        records = [unpack(r) for r in db.execute('SELECT * FROM assessments ORDER BY created_at DESC, rowid DESC LIMIT 500')]
        total = db.execute('SELECT COUNT(*) FROM assessments').fetchone()[0]
    return records, total

def review(record_id, request):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT status,version,mode FROM assessments WHERE id=?', (record_id,)).fetchone()
        if row is None:
            return 'missing'
        if row['status'] != 'completed':
            return 'failed'
        if row['version'] != request.expected_version:
            return 'conflict'
        if row['mode'] == 'live' and request.action == 'APPROVED' and set(request.checks_completed) != {'source_facts','contradictions','actionability'}:
            return 'checklist'
        note = request.note
        if row['mode'] == 'live' and request.action == 'APPROVED':
            note += '\nHuman checklist acknowledged: source facts, contradictions, actionability.'
        db.execute('INSERT INTO reviews(assessment_id,created_at,reviewer,action,note) VALUES(?,?,?,?,?)',
            (record_id, now(), request.reviewer, request.action, note))
        db.execute('UPDATE assessments SET review_status=?,version=version+1 WHERE id=?', (request.action, record_id))
    return 'ok'
