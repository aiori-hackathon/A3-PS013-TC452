import base64
import hashlib
import json
from io import BytesIO
from pathlib import Path
import pytest
from pypdf import PdfReader
from alibi.parsers import parse_bytes, parse_line
from alibi.main import create_app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3] / 'datasets'
TRUTH = json.loads((ROOT / 'ground_truth.json').read_text())
LINE = b'Oct 28 04:42:54 host-a sshd[101]: Accepted publickey for analyst from 198.51.100.24 port 49812\r\n'


def upload(client, case, content=LINE, filename='auth.log', **options):
    settings = dict(source='Host A', timezone='UTC', year=2026, **options)
    return client.post(f'/api/investigations/{case}/evidence', files={'file': (filename, content, 'text/plain')}, data={'options': json.dumps(settings)})


@pytest.mark.parametrize('scenario', TRUTH)
def test_scenarios_end_to_end(client, case, scenario):
    truth = TRUTH[scenario]
    prefix = f'/api/investigations/{case}'
    for source in truth['files']:
        options = {k: v for k, v in source.items() if k != 'filename'}
        options['correction_reason'] = 'Synthetic ground-truth clock measurement'
        data = (ROOT / scenario / source['filename']).read_bytes()
        response = client.post(prefix + '/evidence', files={'file': (source['filename'], data)}, data={'options': json.dumps(options)})
        assert response.status_code == 201, response.text
        item = response.json()
        assert item['sha256'] == hashlib.sha256(data).hexdigest()
        assert client.get(prefix + f"/evidence/{item['id']}/original").content == data
        assert item['total_records'] == item['parsed_records'] + item['gap_records']
    timeline = client.get(prefix + '/timeline').json()
    assert timeline['total'] == truth['parsed']
    assert {e['filename'] + ':' + str(e['line_number']): e['corrected_timestamp'] for e in timeline['items']} == truth['expected_times']
    times = [r['corrected_timestamp'] for r in timeline['items']]
    assert times == sorted(times)
    gaps = client.get(prefix + '/gaps').json()
    assert len(gaps) == truth['gaps']
    for record in timeline['items'] + gaps:
        detail = client.get(prefix + '/records/' + record['id']).json()
        data = (ROOT / scenario / record['filename']).read_bytes()
        assert base64.b64decode(detail['source_bytes_base64']) == data[record['byte_start']:record['byte_end']]
    assert all(v['status'] == 'verified' for v in client.post(prefix + '/verify').json())
    report = client.get(prefix + '/report.json').json()
    assert len(report['timeline']) == truth['parsed'] and len(report['gaps']) == truth['gaps']
    manifest = client.get(prefix + '/manifest.json').json()
    assert len(manifest['files']) == 2
    pdf = client.get(prefix + '/report.pdf')
    assert pdf.content.startswith(b'%PDF')
    text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
    assert 'Chronology' in text and 'SHA-256' in text
    assert 'limitations' in text
    if scenario == 'C_gaps_conflicts':
        assert {f['type'] for f in report['findings']} == {'conflicting_identifier', 'source_order_conflict'}


def test_tamper_detection(client, case):
    evidence = upload(client, case).json()
    path = client.app.state.store.vault / evidence['id']
    path.chmod(0o666)
    path.write_bytes(b'tampered')
    prefix = f'/api/investigations/{case}'
    assert client.post(prefix + '/verify').json()[0]['status'] == 'mismatch'
    assert client.get(prefix + f"/evidence/{evidence['id']}/original").status_code == 409
    record = client.get(prefix + '/timeline').json()['items'][0]
    detail = client.get(prefix + '/records/' + record['id']).json()
    assert detail['source_bytes_base64'] is None
    assert client.get(prefix + '/report.json').json()['integrity'][0]['status'] == 'mismatch'


def test_missing_original(client, case):
    evidence = upload(client, case).json()
    path = client.app.state.store.vault / evidence['id']
    path.chmod(0o666)
    path.unlink()
    assert client.post(f'/api/investigations/{case}/verify').json()[0]['status'] == 'unavailable'


def test_clock_is_absolute_and_audited(client, case):
    evidence = upload(client, case).json()
    prefix = f'/api/investigations/{case}'
    for _ in range(2):
        assert client.patch(prefix + f"/evidence/{evidence['id']}/clock", json={'offset_seconds': 73, 'uncertainty_seconds': 2, 'reason': 'Measured clock delta'}).status_code == 200
    event = client.get(prefix + '/timeline').json()['items'][0]
    assert event['utc_timestamp'] == '2026-10-28T04:42:54.000000Z'
    assert event['corrected_timestamp'] == '2026-10-28T04:44:07.000000Z'
    assert event['interval_start'] == '2026-10-28T04:44:05.000000Z'
    assert event['interval_end'] == '2026-10-28T04:44:09.000000Z'
    assert client.get(prefix + f"/evidence/{evidence['id']}/original").content == LINE
    assert sum(a['action'] == 'clock.corrected' for a in client.get(prefix + '/audit').json()) == 2


@pytest.mark.parametrize('filename', ['../evil.log', '..\\evil.log', 'C:evil.log', '..', 'bad\nname.log'])
def test_path_traversal(client, case, filename):
    assert upload(client, case, filename=filename).status_code == 400


def test_validation_and_isolation(client, case):
    assert upload(client, case, content=b'').status_code == 400
    assert upload(client, case, content=b'x' * (10 * 1024 * 1024 + 1)).status_code == 413
    assert upload(client, case, content=b'\n' * 50001).status_code == 413
    assert client.post('/api/investigations', json={'name': ' '}).status_code == 422
    assert client.post('/api/investigations', json={'name': 'x'}, headers={'Origin': 'https://attacker.example'}).status_code == 403
    item = upload(client, case).json()
    other = client.post('/api/investigations', json={'name': 'Other'}).json()['id']
    assert client.get(f"/api/investigations/{other}/evidence/{item['id']}/original").status_code == 404
    assert client.patch(f"/api/investigations/{other}/evidence/{item['id']}/clock", json={'offset_seconds': 1, 'reason': 'test'}).status_code == 404


def test_search_filter_pagination_persistence(client, case):
    item = upload(client, case).json()
    prefix = f'/api/investigations/{case}'
    assert client.get(prefix + '/timeline', params={'q': 'ANALYST', 'kind': 'auth', 'evidence_id': item['id']}).json()['total'] == 1
    assert client.get(prefix + '/timeline', params={'q': "' OR 1=1 --"}).json()['total'] == 0
    assert client.get(prefix + '/timeline', params={'offset': 1, 'limit': 1}).json()['items'] == []
    assert client.get(prefix + '/timeline', params={'start': '2026-10-28T05:00:00Z'}).json()['total'] == 0
    assert client.get(prefix + '/timeline', params={'start': '2026-10-28T05:00:00'}).status_code == 422
    with TestClient(create_app(client.app.state.store.root)) as fresh:
        assert fresh.get(prefix + '/timeline').json()['total'] == 1


@pytest.mark.parametrize('zone,expected', [('Asia/Kolkata', '2026-10-27T23:12:54.000000Z'), ('-04:00', '2026-10-28T08:42:54.000000Z'), ('UTC', '2026-10-28T04:42:54.000000Z')])
def test_timezone(zone, expected):
    assert parse_line(LINE.decode().strip(), 'syslog', zone, 2026)['utc_timestamp'] == expected


@pytest.mark.parametrize('line,zone,year,reason', [
    ('Nov 01 01:30:00 host sshd: test', 'America/New_York', 2026, 'Ambiguous'),
    ('Mar 08 02:30:00 host sshd: test', 'America/New_York', 2026, 'Nonexistent'),
    ('Oct 28 04:42:54 host sshd: test', 'UTC', None, 'no year'),
    ('Feb 30 04:42:54 host sshd: test', 'UTC', 2026, 'day'),
])
def test_timestamp_failures_become_gaps(line, zone, year, reason):
    result = list(parse_bytes(line.encode(), 'syslog', zone, year))[0]
    assert reason in result['error']


def test_all_bytes_accounted():
    data = LINE + b'\n\xffoops\nunsupported\rfinal'
    records = list(parse_bytes(data, 'auto', 'UTC', 2026))
    assert records[0]['byte_start'] == 0 and records[-1]['byte_end'] == len(data)
    assert all(a['byte_end'] == b['byte_start'] for a, b in zip(records, records[1:]))
    assert sum(r['error'] is not None for r in records) == 4


def test_explicit_timezone_overrides_assumption():
    line = '2026-10-28T10:14:07+05:30 host sshd: test'
    assert parse_line(line, 'syslog', 'America/New_York', 2000)['utc_timestamp'] == '2026-10-28T04:44:07.000000Z'


def test_pdf_untrusted_markup(client, case):
    upload(client, case, content=b'Oct 28 04:42:54 host sshd: <script>& malicious <b>tag\n')
    assert client.get(f'/api/investigations/{case}/report.pdf').status_code == 200


def test_pdf_readable_summary_preserves_json_audit(client, case):
    item = upload(client, case).json()
    prefix = f'/api/investigations/{case}'
    before = client.get(prefix + '/report.json').json()
    rendered = client.get(prefix + '/report.pdf')
    assert rendered.status_code == 200
    text = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(rendered.content)).pages)
    for heading in ('1. Investigation identification', '2. Investigation overview',
                    '3. Evidence integrity summary', '4. Chronology',
                    '5. Clock corrections', '6. Parsing gaps',
                    '7. Evidence references and limitations'):
        assert heading in text
    assert item['sha256'] in text
    assert 'full history in JSON' in text
    assert '"investigation_id":' not in text
    assert before['audit'] == client.get(prefix + '/report.json').json()['audit']
    path = client.app.state.store.vault / item['id']
    path.chmod(0o666)
    path.write_bytes(b'altered fixture')
    failed_pdf = client.get(prefix + '/report.pdf')
    failed_text = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(failed_pdf.content)).pages)
    assert 'MISMATCH' in failed_text and '1 failed or unavailable' in failed_text
