"""Benchmark a byte-exact prefix of public Elastic NGINX data; no parser changes."""
import argparse
import hashlib
import json
import platform
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--commit', required=True)
    p.add_argument('--source-file', type=Path, help='Previously downloaded unchanged source; otherwise download pinned source')
    p.add_argument('--records', type=int, default=1000)
    p.add_argument('--runs', type=int, default=3)
    p.add_argument('--url', default='http://127.0.0.1:8000')
    args = p.parse_args()
    assert 1 <= args.records <= 50000 and 1 <= args.runs <= 10
    out = ROOT / 'output/external'
    out.mkdir(parents=True, exist_ok=True)
    source_url = f'https://raw.githubusercontent.com/elastic/examples/{args.commit}/Common%20Data%20Formats/nginx_logs/nginx_logs'
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        if args.source_file:
            original = args.source_file.read_bytes()
        else:
            response = client.get(source_url)
            response.raise_for_status()
            original = response.content
            (out / 'nginx_logs.original').write_bytes(original)
        lines = original.splitlines(keepends=True)
        subset = b''.join(lines[:args.records])
        count = len(lines[:args.records])
        assert len(subset) <= 10 * 1024 * 1024 and original.startswith(subset)
        (out / 'nginx-prefix.log').write_bytes(subset)
        digest = hashlib.sha256(subset).hexdigest()
        runs = []
        for n in range(args.runs):
            response = client.post(args.url + '/api/investigations', json={'name': f'EXTERNAL / Elastic NGINX / run {n+1}', 'description': f'Published sample at {args.commit}; unchanged first {count} records. Parsing coverage only, no incident ground truth.'})
            response.raise_for_status()
            case = response.json()['id']
            prefix = args.url + '/api/investigations/' + case
            started = perf_counter()
            response = client.post(prefix + '/evidence', files={'file': ('nginx-prefix.log', subset)}, data={'options': json.dumps({'source': 'Elastic NGINX sample', 'log_format': 'auto', 'timezone': 'UTC', 'offset_seconds': 0})})
            response.raise_for_status()
            elapsed = perf_counter() - started
            item = response.json()
            assert item['parsed_records'] + item['gap_records'] == count
            assert item['sha256'] == digest
            assert client.get(prefix + '/evidence/' + item['id'] + '/original').content == subset
            verification = client.post(prefix + '/verify')
            verification.raise_for_status()
            assert all(v['status'] == 'verified' for v in verification.json())
            started = perf_counter()
            response = client.get(prefix + '/timeline', params={'q': 'GET', 'limit': 50})
            response.raise_for_status()
            query_seconds = perf_counter() - started
            result = response.json()
            assert result['total'] > 0 and all('GET' in e['message'] for e in result['items'])
            runs.append({'run': n+1, 'investigation_id': case, 'input_records': count, 'normalized': item['parsed_records'], 'gaps': item['gap_records'], 'coverage_percent': 100*item['parsed_records']/count, 'import_seconds': elapsed, 'records_per_second': count/elapsed, 'query_seconds': query_seconds, 'query_matches': result['total'], 'integrity': 'verified', 'original_download_matches': True})
        started = perf_counter()
        response = client.get(prefix + '/report.pdf')
        response.raise_for_status()
        pdf_seconds = perf_counter() - started
        assert response.content.startswith(b'%PDF')
        (out / 'report.pdf').write_bytes(response.content)
        for name in ('report.json', 'manifest.json'):
            response = client.get(prefix + '/' + name)
            response.raise_for_status()
            (out / name).write_bytes(response.content)
    report = {'dataset': 'Elastic examples / NGINX combined sample logs', 'measured_at': datetime.now(timezone.utc).isoformat(), 'commit': args.commit, 'source_url': source_url, 'source_bytes': len(original), 'source_records': len(lines), 'source_sha256': hashlib.sha256(original).hexdigest(), 'selection': f'First {count} physical lines, splitlines(keepends=True), exact unchanged byte prefix', 'subset_bytes': len(subset), 'subset_sha256': digest, 'runs': runs, 'median_import_seconds': statistics.median(r['import_seconds'] for r in runs), 'median_records_per_second': statistics.median(r['records_per_second'] for r in runs), 'median_query_seconds': statistics.median(r['query_seconds'] for r in runs), 'pdf_seconds_single_run': pdf_seconds, 'environment': {'python': sys.version.split()[0], 'os': platform.platform(), 'processor': platform.processor(), 'timer': 'time.perf_counter', 'transport': 'local HTTP; same running backend and SQLite; fresh investigation per run'}, 'limitations': ['Three sequential fresh-investigation runs, not independent machines/process restarts; warm caches possible.', 'Prefix selection is reproducible, not random or representative.', 'Coverage is parser acceptance, not incident detection accuracy.', 'No labeled incident ground truth; automated runtime is not human investigation time.', 'Import timing includes HTTP upload, preservation, parsing and persistence; excludes download, case creation, verification and report generation.', 'PDF timing is one run; search is GET with a 50-result page.']}
    (ROOT / 'docs/external-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
