import base64
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, Request
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import ValidationError
from .models import InvestigationCreate, IntakeOptions, ClockCorrection, EvidenceRecord, EventRecord, TimelinePage
from .parsers import parse_bytes, utc_text
from .store import Store
from .reports import make_pdf, LIMITATIONS
from .calibration import register_calibration

MAX_UPLOAD = 10 * 1024 * 1024
MAX_RECORDS = 50000
JOIN = 'SELECT r.*, e.filename, e.source, e.offset_seconds, e.uncertainty_seconds FROM records r JOIN evidence e ON e.id=r.evidence_id '


def now():
    return utc_text(datetime.now(timezone.utc))


def corrected(record, offset, uncertainty):
    point = datetime.fromisoformat(record['utc_timestamp'].replace('Z', '+00:00')) + timedelta(seconds=offset)
    return dict(corrected_timestamp=utc_text(point), interval_start=utc_text(point - timedelta(seconds=uncertainty)), interval_end=utc_text(point + timedelta(seconds=uncertainty)))


def create_app(data_dir: Path | None = None):
    store = Store(data_dir or Path(os.environ.get('ALIBI_DATA_DIR', '.alibi')))
    app = FastAPI(title='ALIBI Evidence Workbench', version='0.1.0', docs_url='/api/docs', openapi_url='/api/openapi.json')
    app.state.store = store
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', '[::1]', 'testserver'])

    @app.middleware('http')
    async def local_origin_guard(request: Request, call_next):
        if request.method == 'POST' and request.url.path.endswith('/evidence'):
            length = request.headers.get('content-length')
            if length is None:
                return JSONResponse({'detail': 'Content-Length is required for evidence intake'}, status_code=411)
            if not length.isdigit():
                return JSONResponse({'detail': 'Invalid Content-Length'}, status_code=400)
            if int(length) > MAX_UPLOAD + 1024 * 1024:
                return JSONResponse({'detail': 'Multipart request exceeds 11 MiB limit'}, status_code=413)
        origin = request.headers.get('origin')
        allowed = {'http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:8000', 'http://localhost:8000', 'http://127.0.0.1:4173', 'http://localhost:4173'}
        if origin and origin not in allowed:
            return JSONResponse({'detail': 'Requests from this origin are not allowed'}, status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Cross-site requests are not allowed'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store'
        return response

    def investigation(case_id):
        rows = store.rows('SELECT * FROM investigations WHERE id=?', (case_id,))
        if not rows:
            raise HTTPException(404, 'Investigation not found')
        return rows[0]

    def evidence_item(case_id, evidence_id):
        investigation(case_id)
        rows = store.rows('SELECT * FROM evidence WHERE investigation_id=? AND id=?', (case_id, evidence_id))
        if not rows:
            raise HTTPException(404, 'Evidence not found in this investigation')
        return rows[0]

    def verify(item):
        path = store.vault / item['id']
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            status = 'verified' if actual == item['sha256'] else 'mismatch'
        except OSError:
            actual, status = None, 'unavailable'
        return dict(evidence_id=item['id'], filename=item['filename'], expected_sha256=item['sha256'], actual_sha256=actual, status=status, checked_at=now())

    @app.get('/api/health')
    def health():
        store.rows('SELECT 1')
        return {'status': 'ok', 'version': '0.1.0', 'storage': 'sqlite', 'local_only': True}

    @app.get('/api/investigations')
    def cases():
        return store.rows('SELECT * FROM investigations ORDER BY created_at DESC')

    @app.post('/api/investigations', status_code=201)
    def create_case(body: InvestigationCreate):
        item = body.model_dump() | {'id': str(uuid.uuid4()), 'created_at': now()}
        with store.connect() as db:
            store.insert(db, 'investigations', item)
            store.audit(db, item['id'], 'investigation.created', body.model_dump(), now())
        return item

    @app.get('/api/investigations/{case_id}/evidence', response_model=list[EvidenceRecord])
    def list_evidence(case_id: str):
        investigation(case_id)
        return store.rows('SELECT * FROM evidence WHERE investigation_id=? ORDER BY imported_at,id', (case_id,))

    @app.post('/api/investigations/{case_id}/evidence', status_code=201, response_model=EvidenceRecord)
    def intake(case_id: str, file: UploadFile = File(...), options: str = Form(...)):
        investigation(case_id)
        try:
            settings = IntakeOptions.model_validate_json(options)
        except ValidationError as exc:
            raise HTTPException(422, json.loads(exc.json(include_url=False, include_context=False))) from exc
        name = file.filename or ''
        if not name or len(name) > 240 or any(c in name for c in '/\\\x00\r\n') or name in ('.', '..') or ':' in name:
            raise HTTPException(400, 'Upload must have a plain filename without paths or control characters')
        if any(ord(c) < 32 for c in name) or re.search(r'%(?:0[0-9a-f]|1[0-9a-f]|2f|5c)', name, re.I):
            raise HTTPException(400, 'Invalid filename')
        data = file.file.read(MAX_UPLOAD + 1)
        if not data:
            raise HTTPException(400, 'Empty evidence file')
        if len(data) > MAX_UPLOAD:
            raise HTTPException(413, 'Evidence file exceeds 10 MiB limit')
        if data.count(b'\n') > MAX_RECORDS or data.count(b'\r') > MAX_RECORDS:
            raise HTTPException(413, 'Evidence exceeds 50,000 record limit; split the source into documented parts')
        records = list(parse_bytes(data, settings.log_format, settings.timezone, settings.year))
        if len(records) > MAX_RECORDS:
            raise HTTPException(413, 'Evidence exceeds 50,000 record limit')
        evidence_id = str(uuid.uuid4())
        parsed_count = sum(r['error'] is None for r in records)
        item = settings.model_dump() | dict(id=evidence_id, investigation_id=case_id, filename=name, sha256=hashlib.sha256(data).hexdigest(), size=len(data), imported_at=now(), total_records=len(records), parsed_records=parsed_count, gap_records=len(records)-parsed_count)
        # UUID-only storage name, exclusive creation; no API can replace originals.
        path = store.vault / evidence_id
        with path.open('xb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        path.chmod(0o444)
        with store.connect() as db:
            store.insert(db, 'evidence', item)
            for record in records:
                record.update(id=str(uuid.uuid4()), evidence_id=evidence_id, investigation_id=case_id)
                if record['error'] is None:
                    record.update(corrected(record, settings.offset_seconds, settings.uncertainty_seconds))
                store.insert(db, 'records', record)
            store.audit(db, case_id, 'evidence.imported', item, now())
        return item

    @app.get('/api/investigations/{case_id}/timeline', response_model=TimelinePage)
    def timeline(case_id: str, q: str = Query('', max_length=500), evidence_id: str | None = None, kind: str | None = None, start: datetime | None = None, end: datetime | None = None, limit: int = Query(200, ge=1, le=1000), offset: int = Query(0, ge=0)):
        investigation(case_id)
        clause = ' WHERE r.investigation_id=? AND r.error IS NULL'
        params = [case_id]
        if q:
            clause += " AND (instr(lower(r.raw_line),lower(?))>0 OR instr(lower(e.source),lower(?))>0)"
            params += [q, q]
        for column, value in [('r.evidence_id', evidence_id), ('r.kind', kind)]:
            if value:
                clause += f' AND {column}=?'
                params.append(value)
        for op, value in [('>=', start), ('<=', end)]:
            if value:
                if value.tzinfo is None:
                    raise HTTPException(422, 'Time filters require an explicit timezone')
                clause += f' AND r.corrected_timestamp {op} ?'
                params.append(utc_text(value))
        total = store.rows('SELECT count(*) AS n FROM records r JOIN evidence e ON e.id=r.evidence_id' + clause, params)[0]['n']
        rows = store.rows(JOIN + clause + ' ORDER BY r.corrected_timestamp,r.evidence_id,r.line_number LIMIT ? OFFSET ?', params + [limit, offset])
        return {'items': rows, 'total': total, 'limit': limit, 'offset': offset}

    @app.get('/api/investigations/{case_id}/gaps', response_model=list[EventRecord])
    def gaps(case_id: str):
        investigation(case_id)
        return store.rows(JOIN + ' WHERE r.investigation_id=? AND r.error IS NOT NULL ORDER BY e.imported_at,r.line_number', (case_id,))

    @app.get('/api/investigations/{case_id}/records/{record_id}')
    def detail(case_id: str, record_id: str):
        rows = store.rows(JOIN + ' WHERE r.investigation_id=? AND r.id=?', (case_id, record_id))
        if not rows:
            raise HTTPException(404, 'Record not found')
        record = rows[0]
        item = evidence_item(case_id, record['evidence_id'])
        check = verify(item)
        source = None
        if check['status'] == 'verified':
            with (store.vault / item['id']).open('rb') as stream:
                stream.seek(record['byte_start'])
                source = base64.b64encode(stream.read(record['byte_end'] - record['byte_start'])).decode('ascii')
        return record | {'source_bytes_base64': source, 'integrity': check}

    @app.get('/api/investigations/{case_id}/evidence/{evidence_id}/original')
    def original(case_id: str, evidence_id: str):
        item = evidence_item(case_id, evidence_id)
        if verify(item)['status'] != 'verified':
            raise HTTPException(409, 'Original evidence failed verification; inspect integrity report')
        return FileResponse(store.vault / item['id'], media_type='application/octet-stream', filename=item['filename'])

    @app.post('/api/investigations/{case_id}/verify')
    def verify_case(case_id: str):
        results = [verify(e) for e in list_evidence(case_id)]
        with store.connect() as db:
            store.audit(db, case_id, 'evidence.verified', results, now())
        return results

    @app.patch('/api/investigations/{case_id}/evidence/{evidence_id}/clock')
    def clock(case_id: str, evidence_id: str, body: ClockCorrection):
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT * FROM evidence WHERE id=? AND investigation_id=?', (evidence_id, case_id)).fetchone()
            if previous is None:
                raise HTTPException(404, 'Evidence not found')
            records = db.execute('SELECT * FROM records WHERE evidence_id=? AND error IS NULL', (evidence_id,)).fetchall()
            for record in records:
                times = corrected(record, body.offset_seconds, body.uncertainty_seconds)
                db.execute('UPDATE records SET corrected_timestamp=?,interval_start=?,interval_end=? WHERE id=?', (*times.values(), record['id']))
            db.execute('UPDATE evidence SET offset_seconds=?,uncertainty_seconds=?,correction_reason=? WHERE id=?', (body.offset_seconds, body.uncertainty_seconds, body.reason, evidence_id))
            store.audit(db, case_id, 'clock.corrected', {'evidence_id': evidence_id, 'before': dict(previous), 'after': body.model_dump()}, now())
        return evidence_item(case_id, evidence_id)

    @app.get('/api/investigations/{case_id}/findings')
    def findings(case_id: str):
        investigation(case_id)
        records = store.rows(JOIN + ' WHERE r.investigation_id=? AND r.error IS NULL ORDER BY r.evidence_id,r.line_number', (case_id,))
        result, previous, identities = [], {}, {}
        for event in records:
            last = previous.get(event['evidence_id'])
            if last and event['utc_timestamp'] < last['utc_timestamp']:
                result.append({'type': 'source_order_conflict', 'message': 'Timestamp moves backwards within this source. Check clock changes, file ordering, and year assumptions.', 'record_ids': [last['id'], event['id']]})
            previous[event['evidence_id']] = event
            if event['anchor_id']:
                key = (event['evidence_id'], event['anchor_id'])
                old = identities.get(key)
                if old and old['status'] and event['status'] and old['status'] != event['status']:
                    result.append({'type': 'conflicting_identifier', 'message': f"Identifier {event['anchor_id']} has differing HTTP statuses within one source. May be reuse, retries, or contradictory records; investigate.", 'record_ids': [old['id'], event['id']]})
                identities[key] = event
        return result

    @app.get('/api/investigations/{case_id}/audit')
    def audit(case_id: str):
        investigation(case_id)
        return store.rows('SELECT * FROM audit WHERE investigation_id=? ORDER BY id', (case_id,))

    relationships, proposals = register_calibration(app, store, investigation, evidence_item, now, corrected, verify)

    def build_report(case_id):
        evidence = list_evidence(case_id)
        return {'schema_version': '1.0', 'generated_at': now(), 'investigation': investigation(case_id), 'evidence': evidence,
                'timeline': store.rows(JOIN + ' WHERE r.investigation_id=? AND r.error IS NULL ORDER BY r.corrected_timestamp,r.evidence_id,r.line_number', (case_id,)),
                'gaps': gaps(case_id), 'findings': findings(case_id), 'relationships': relationships(case_id), 'calibration_proposals': proposals(case_id), 'integrity': [verify(e) for e in evidence], 'audit': audit(case_id), 'limitations': LIMITATIONS}

    @app.get('/api/investigations/{case_id}/report.json')
    def json_report(case_id: str):
        return Response(json.dumps(build_report(case_id), indent=2, ensure_ascii=False), media_type='application/json', headers={'Content-Disposition': 'attachment; filename="alibi-report.json"'})

    @app.get('/api/investigations/{case_id}/report.pdf')
    def pdf_report(case_id: str):
        return Response(make_pdf(build_report(case_id)), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="alibi-report.pdf"'})

    @app.get('/api/investigations/{case_id}/manifest.json')
    def manifest(case_id: str):
        evidence = list_evidence(case_id)
        return Response(json.dumps({'algorithm': 'SHA-256', 'generated_at': now(), 'investigation_id': case_id, 'files': [dict(evidence_id=e['id'], filename=e['filename'], size=e['size'], sha256=e['sha256'], vault_relative_path='evidence/' + e['id']) for e in evidence], 'verification': [verify(e) for e in evidence]}, indent=2), media_type='application/json', headers={'Content-Disposition': 'attachment; filename="alibi-manifest.json"'})

    return app


app = create_app()
