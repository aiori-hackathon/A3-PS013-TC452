import base64
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "datasets/D_realistic_incident"
SPEC = json.loads((DATA/"ground_truth.json").read_text(encoding="utf-8-sig"))


def test_scenario_d_reproducible(tmp_path):
    subprocess.run([sys.executable, str(ROOT/"scripts/generate_scenario_d.py"), "--out", str(tmp_path)], check=True)
    assert sorted(f.name for f in tmp_path.iterdir()) == ["access.log", "auth.log", "system.log"]
    for file in tmp_path.iterdir():
        assert file.read_bytes() == (DATA/file.name).read_bytes()


def test_d_ground_truth_and_package(client, case, tmp_path):
    prefix = "/api/investigations/" + case
    for file in SPEC["files"]:
        name = file["filename"]
        response = client.post(prefix + "/evidence", files={"file": (name, (DATA/name).read_bytes())},
                               data={"options": json.dumps({k:v for k,v in file.items() if k != "filename"})})
        assert response.status_code == 201, response.text
    report = client.get(prefix + "/report.json").json()
    assert len({f["source"] for f in report["evidence"]}) == SPEC["source_count"]
    assert sum(f["total_records"] for f in report["evidence"]) == SPEC["physical_records"]
    assert len(report["timeline"]) == SPEC["normalized"] and len(report["gaps"]) == SPEC["gaps"]
    observed = {(r["filename"],r["line_number"]):r["corrected_timestamp"] for r in report["timeline"] + report["gaps"]}
    expected = {(name,n):f"{SPEC['utc_date']}T{stamp}.000000Z" if stamp else None
                for name,times in SPEC["corrected_utc_by_line"].items() for n,stamp in enumerate(times,1)}
    assert observed == expected
    assert len(report["findings"]) == 5
    login, = [f for f in report["findings"] if f["type"] == "authentication_sequence"]
    assert [r["line_number"] for r in login["references"]] == [5,8]
    detail = client.get(prefix+"/records/"+login["record_ids"][1]).json()
    assert detail["original_timestamp"] == "Nov 19 05:02:35"
    assert detail["interval_start"].endswith("05:04:03.000000Z") and detail["interval_end"].endswith("05:04:07.000000Z")
    assert base64.b64decode(detail["source_bytes_base64"]) == (DATA/"auth.log").read_bytes().splitlines(keepends=True)[7]
    response = client.get(prefix+"/case.zip")
    assert response.is_success
    path = tmp_path/"case.zip"
    path.write_bytes(response.content)
    subprocess.run([sys.executable,str(ROOT/"scripts/verify_case.py"),str(path)],check=True)
