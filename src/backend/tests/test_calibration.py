import json
from datetime import datetime, timedelta, timezone


def seed(client, case, count=3, jitter=0, spacing=60, duplicate=False):
    evidence = []
    for source, shift in [('reference', 0), ('target', -73)]:
        lines = []
        for i in range(count):
            dt = datetime(2026,10,28,4,44,7,tzinfo=timezone.utc)+timedelta(seconds=i*spacing+shift+(jitter if i==count-1 and source=='target' else 0))
            lines.append(f'{dt.isoformat()} {source} service: observed same fixture event event_id=E{i}\n')
        if duplicate:
            lines.append(lines[0])
        response = client.post(f'/api/investigations/{case}/evidence', files={'file':(source+'.log',''.join(lines).encode())}, data={'options':json.dumps({'source':source})})
        assert response.status_code == 201
        evidence.append(response.json()['id'])
    return {'reference_id':evidence[0], 'evidence_id':evidence[1], 'same_event_basis':'Synthetic fixture explicitly records identical events on two clocks with no added latency.'}


def test_preview_apply_and_audit(client, case):
    body = seed(client, case)
    prefix = f'/api/investigations/{case}'
    response = client.post(prefix+'/calibration/proposals',json=body)
    assert response.status_code == 201
    proposal = response.json()
    assert proposal['offset_seconds'] == 73 and proposal['uncertainty_seconds'] == 1
    assert next(e for e in client.get(prefix+'/evidence').json() if e['id']==body['evidence_id'])['offset_seconds']==0
    endpoint = prefix+'/calibration/proposals/'+proposal['id']+'/approve'
    assert client.post(endpoint,json={'reason':'Investigator reviewed same-event anchors'}).status_code == 200
    assert client.post(endpoint,json={'reason':'Investigator reviewed same-event anchors'}).status_code == 409
    assert len(client.get(prefix+'/relationships').json()) == 3
    assert client.get(prefix+'/report.json').json()['calibration_proposals'][0]['status']=='applied'


def test_stale_reference_rejected(client, case):
    body=seed(client,case)
    prefix=f'/api/investigations/{case}'
    proposal=client.post(prefix+'/calibration/proposals',json=body).json()
    client.patch(prefix+'/evidence/'+body['reference_id']+'/clock',json={'offset_seconds':1,'reason':'Reference clock changed'})
    assert client.post(prefix+'/calibration/proposals/'+proposal['id']+'/approve',json={'reason':'Review completed'}).status_code==409


def test_insufficient_anchors(client, case):
    body=seed(client,case,count=2)
    assert client.post(f'/api/investigations/{case}/calibration/proposals',json=body).status_code==422


def test_inconsistent_anchors(client, case):
    body=seed(client,case,jitter=10)
    assert client.post(f'/api/investigations/{case}/calibration/proposals',json=body).status_code==422


def test_duplicate_and_short_span(client, case):
    body=seed(client,case,duplicate=True)
    assert client.post(f'/api/investigations/{case}/calibration/proposals',json=body).status_code==422
    body=seed(client,case,spacing=10)
    assert client.post(f'/api/investigations/{case}/calibration/proposals',json=body).status_code==422


def test_tampered_anchor_rejected(client, case):
    body=seed(client,case)
    prefix=f'/api/investigations/{case}'
    proposal=client.post(prefix+'/calibration/proposals',json=body).json()
    path=client.app.state.store.vault/body['reference_id']
    path.chmod(0o666)
    path.write_bytes(b'changed')
    assert client.post(prefix+'/calibration/proposals',json=body).status_code==409
    assert client.post(prefix+'/calibration/proposals/'+proposal['id']+'/approve',json={'reason':'Reviewed anchors'}).status_code==409
