"""Independently verify an exported manifest against the local ALIBI vault."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('manifest', type=Path)
parser.add_argument('--data-dir', type=Path, default=Path('.alibi'))
args = parser.parse_args()
root = args.data_dir.resolve()
manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
failed = False
for item in manifest['files']:
    path = (root / item['vault_relative_path']).resolve()
    if not path.is_relative_to(root / 'evidence'):
        raise SystemExit('Manifest path is outside the evidence vault')
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    ok = actual == item['sha256']
    failed |= not ok
    print(('VERIFIED' if ok else 'FAILED') + ' ' + item['evidence_id'] + ' / ' + item['filename'])
raise SystemExit(1 if failed else 0)
