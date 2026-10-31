"""Real HTTP smoke: imports all fixtures, verifies truth, exports demo artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    truth = json.loads((ROOT / 'datasets/ground_truth.json').read_text())
    output = ROOT / 'output'
    (output / 'pdf').mkdir(parents=True, exist_ok=True)
    results = []
    with httpx.Client(base_url=args.url, timeout=60) as client:
        assert client.get('/api/health').json()['status'] == 'ok'
        for scenario, spec in truth.items():
            started = perf_counter()
            response = client.post('/api/investigations', json={'name': 'SYNTHETIC / ' + scenario.replace('_', ' '), 'description': spec['description']})
            response.raise_for_status()
            case_id = response.json()['id']
            prefix = '/api/investigations/' + case_id
            for item in spec['files']:
                data = (ROOT / 'datasets' / scenario / item['filename']).read_bytes()
                options = {k: v for k, v in item.items() if k != 'filename'}
                options['correction_reason'] = 'Known synthetic ground-truth clock offset'
                imported = client.post(prefix + '/evidence', files={'file': (item['filename'], data)}, data={'options': json.dumps(options)})
                imported.raise_for_status()
                evidence = imported.json()
                assert evidence['sha256'] == hashlib.sha256(data).hexdigest()
                assert client.get(prefix + '/evidence/' + evidence['id'] + '/original').content == data
            timeline = client.get(prefix + '/timeline').json()
            assert timeline['total'] == spec['parsed']
            assert {e['filename'] + ':' + str(e['line_number']): e['corrected_timestamp'] for e in timeline['items']} == spec['expected_times']
            assert len(client.get(prefix + '/gaps').json()) == spec['gaps']
            assert all(item['status'] == 'verified' for item in client.post(prefix + '/verify').json())
            for export in ('report.json', 'report.pdf', 'manifest.json'):
                response = client.get(prefix + '/' + export)
                response.raise_for_status()
                destination = output / ('pdf' if export.endswith('.pdf') else 'json')
                destination.mkdir(exist_ok=True)
                (destination / f'{scenario}-{export}').write_bytes(response.content)
            results.append({'scenario': scenario, 'investigation_id': case_id, 'elapsed_seconds': round(perf_counter()-started, 4), 'parsed': spec['parsed'], 'gaps': spec['gaps'], 'status': 'passed'})
    result = {'kind': 'automated pipeline runtime, NOT human triage time', 'manual_baseline': 'not measured', 'results': results}
    (output / 'smoke-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
