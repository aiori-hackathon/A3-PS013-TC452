"""Optional, investigator-reviewed constant clock model; no causal inference."""
import json
import uuid
from collections import defaultdict
from datetime import datetime
from statistics import median
from fastapi import HTTPException
from pydantic import Field
from .models import StrictModel, ClockCorrection


class ProposalRequest(StrictModel):
    evidence_id: str
    reference_id: str
    same_event_basis: str = Field(min_length=20, max_length=2000)


class Approval(StrictModel):
    reason: str = Field(min_length=10, max_length=2000)


def stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def snapshot(item):
    return {k: item[k] for k in ('id', 'sha256', 'offset_seconds', 'uncertainty_seconds', 'correction_reason')}


def register_calibration(app, store, investigation, evidence_item, now, corrected, verify):
    @app.get('/api/investigations/{case_id}/relationships')
    def relationships(case_id: str):
        investigation(case_id)
        rows = store.rows("SELECT id,evidence_id,anchor_id FROM records WHERE investigation_id=? AND error IS NULL AND anchor_id != ''", (case_id,))
        groups = defaultdict(list)
        for row in rows:
            groups[row['anchor_id']].append(row)
        return [{'type': 'shared_identifier', 'identifier': key, 'record_ids': [r['id'] for r in records], 'message': 'Shared identifier only; same event, actor identity, and causation are not established.'} for key, records in groups.items() if len({r['evidence_id'] for r in records}) > 1]

    @app.post('/api/investigations/{case_id}/calibration/proposals', status_code=201)
    def propose(case_id: str, body: ProposalRequest):
        if body.evidence_id == body.reference_id:
            raise HTTPException(422, 'Choose two different evidence files')
        target = evidence_item(case_id, body.evidence_id)
        reference = evidence_item(case_id, body.reference_id)
        if any(verify(item)['status'] != 'verified' for item in (target, reference)):
            raise HTTPException(409, 'Both original files must pass integrity verification before calibration')
        if target['source'] == reference['source']:
            raise HTTPException(422, 'Anchors must come from distinct source labels')
        def unique(evidence_id):
            grouped = defaultdict(list)
            for row in store.rows("SELECT * FROM records WHERE evidence_id=? AND error IS NULL AND anchor_id != ''", (evidence_id,)):
                grouped[row['anchor_id']].append(row)
            return {key: values[0] for key, values in grouped.items() if len(values) == 1}
        targets, references = unique(target['id']), unique(reference['id'])
        pairs = []
        for identifier in sorted(targets.keys() & references.keys()):
            a, b = targets[identifier], references[identifier]
            delta = (stamp(b['corrected_timestamp']) - stamp(a['utc_timestamp'])).total_seconds()
            pairs.append({'identifier': identifier, 'target_record_id': a['id'], 'reference_record_id': b['id'], 'target_utc': a['utc_timestamp'], 'reference_corrected': b['corrected_timestamp'], 'delta_seconds': delta})
        if len(pairs) < 3:
            raise HTTPException(422, 'Insufficient evidence: need at least three unique matching request_id/event_id anchors. Repeated IDs within either file are excluded.')
        span = (max(stamp(p['target_utc']) for p in pairs)-min(stamp(p['target_utc']) for p in pairs)).total_seconds()
        if span < 60:
            raise HTTPException(422, 'Insufficient temporal coverage: anchors must span at least 60 seconds')
        offset = median(p['delta_seconds'] for p in pairs)
        residual = max(abs(p['delta_seconds']-offset) for p in pairs)
        if residual > 2:
            raise HTTPException(422, 'Anchor residual exceeds 2 seconds; a constant-offset model is not supported')
        uncertainty = residual + reference['uncertainty_seconds'] + 1
        if abs(offset) > 604800 or uncertainty > 86400:
            raise HTTPException(422, 'Proposed model exceeds supported bounds')
        proposal = {'id': str(uuid.uuid4()), 'evidence_id': target['id'], 'reference_id': reference['id'], 'offset_seconds': offset, 'uncertainty_seconds': uncertainty, 'residual_seconds': residual, 'span_seconds': span, 'pairs': pairs, 'same_event_basis': body.same_event_basis, 'target_snapshot': snapshot(target), 'reference_snapshot': snapshot(reference), 'limitation': 'Assumes each pair records the same event with negligible systematic latency and a stable reference clock. Bound = largest residual + supplied reference uncertainty + 1 second resolution allowance; not a statistical confidence interval.'}
        with store.connect() as db:
            db.execute('INSERT INTO calibration_proposals(id,investigation_id,created_at,status,payload) VALUES (?,?,?,?,?)', (proposal['id'], case_id, now(), 'proposed', json.dumps(proposal)))
            store.audit(db, case_id, 'calibration.proposed', proposal, now())
        return proposal | {'status': 'proposed'}

    @app.post('/api/investigations/{case_id}/calibration/proposals/{proposal_id}/approve')
    def approve(case_id: str, proposal_id: str, body: Approval):
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            saved = db.execute('SELECT * FROM calibration_proposals WHERE id=? AND investigation_id=?', (proposal_id, case_id)).fetchone()
            if not saved:
                raise HTTPException(404, 'Proposal not found')
            if saved['status'] != 'proposed':
                raise HTTPException(409, 'Proposal already applied; create a fresh proposal')
            proposal = json.loads(saved['payload'])
            for role in ('target', 'reference'):
                before = proposal[role + '_snapshot']
                current = dict(db.execute('SELECT * FROM evidence WHERE id=? AND investigation_id=?', (before['id'], case_id)).fetchone())
                if snapshot(current) != before:
                    raise HTTPException(409, 'Clock settings changed since preview; create a fresh proposal')
                if verify(current)['status'] != 'verified':
                    raise HTTPException(409, 'Original evidence no longer passes integrity verification')
            target = proposal['evidence_id']
            reason = f"Approved anchor model {proposal_id}. {body.reason}. Same-event basis: {proposal['same_event_basis']}. {proposal['limitation']}"
            for record in db.execute('SELECT * FROM records WHERE evidence_id=? AND error IS NULL', (target,)).fetchall():
                times = corrected(record, proposal['offset_seconds'], proposal['uncertainty_seconds'])
                db.execute('UPDATE records SET corrected_timestamp=?,interval_start=?,interval_end=? WHERE id=?', (*times.values(), record['id']))
            db.execute('UPDATE evidence SET offset_seconds=?,uncertainty_seconds=?,correction_reason=? WHERE id=?', (proposal['offset_seconds'], proposal['uncertainty_seconds'], reason, target))
            db.execute("UPDATE calibration_proposals SET status='applied' WHERE id=?", (proposal_id,))
            store.audit(db, case_id, 'calibration.approved', {'proposal': proposal, 'approval_reason': body.reason}, now())
        return evidence_item(case_id, target)

    @app.get('/api/investigations/{case_id}/calibration/proposals')
    def proposals(case_id: str):
        investigation(case_id)
        return [json.loads(row['payload']) | {'status': row['status'], 'created_at': row['created_at']} for row in store.rows('SELECT * FROM calibration_proposals WHERE investigation_id=? ORDER BY created_at', (case_id,))]

    return relationships, proposals
