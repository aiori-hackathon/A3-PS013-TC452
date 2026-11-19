"""Build a portable case from a consistent report and verified original bytes."""
import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException

VERIFIER = Path(__file__).resolve().parents[3] / "scripts" / "verify_case.py"
INSTRUCTIONS = """ALIBI portable case
1. Keep this ZIP intact. Python 3 can verify it without extracting evidence.
2. Copy verify_case.py beside the ZIP (or use scripts/verify_case.py from ALIBI).
3. Run: python verify_case.py <path-to-case.zip>
4. PASS means the packaged artifacts match the manifest. FAIL means verification failed.
For independent review use a trusted copy of the verifier. A manifest is unsigned:
someone able to replace both evidence and manifest could recompute these hashes.

report.json contains original filenames, source labels, clock assumptions, the timeline,
parsing gaps, investigative leads, provenance, integrity checks and the audit history.
Match each evidence UUID in the manifest with its entry in report.json.
"""


def case_package(report, vault):
    files = []
    target = BytesIO()
    with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=1) as archive:
        def add(path, data, **metadata):
            archive.writestr(path, data)
            files.append(dict(path=path, sha256=hashlib.sha256(data).hexdigest(), size=len(data), **metadata))

        for item, check in zip(report["evidence"], report["integrity"], strict=True):
            try:
                data = (vault / item["id"]).read_bytes()
            except OSError:
                data = None
            if check["status"] != "verified" or data is None or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise HTTPException(409, f"Export stopped: integrity check failed for {item['filename']} ({item['id']}).")
            add("evidence/" + item["id"], data, evidence_id=item["id"], filename=item["filename"], source=item["source"])
        add("report.json", json.dumps(report, ensure_ascii=False, indent=2).encode())
        add("VERIFY.txt", INSTRUCTIONS.encode())
        add("verify_case.py", VERIFIER.read_bytes())
        manifest = dict(format="alibi-case-v1", algorithm="SHA-256", investigation_id=report["investigation"]["id"], files=files)
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode())
    return target.getvalue()
