"""Acceptance tests for corrected-clock leads and independently portable cases."""
import hashlib
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[3]
IP = "203.0.113.8"


def ingest(client, case, data, source, filename="events.log", **options):
    response = client.post(f"/api/investigations/{case}/evidence",
                           files={"file": (filename, data)},
                           data={"options": json.dumps({"source": source, **options})})
    assert response.status_code == 201, response.text
    return response.json()


def ssh(clock, outcome, ip=IP, service="sshd[24]"):
    return f"2026-10-28T{clock}Z host {service}: {outcome} password for user from {ip} port 44\n".encode()


def web(clock, path="/", ip=IP):
    return f'{ip} - - [28/Oct/2026:{clock} +0000] "GET {path} HTTP/1.1" 200 4\n'.encode()


def review(client, case, kind):
    findings = client.get(f"/api/investigations/{case}/findings").json()
    return [f for f in findings if f["type"] == kind]


@pytest.mark.parametrize("clock,ip,service,expected", [
    ("04:45:00", IP, "sshd", 1), ("04:45:01", IP, "sshd", 0),
    ("04:40:00", IP, "sshd", 0), ("04:41:00", "192.0.2.1", "sshd", 0),
    ("04:41:00", "-", "sshd", 0), ("04:41:00", IP, "sshd-test", 0)])
def test_auth_sequence(client, case, clock, ip, service, expected):
    ingest(client, case, ssh("04:40:00", "Failed") + ssh(clock, "Accepted", ip, service), "Linux")
    assert len(review(client, case, "authentication_sequence")) == expected


def test_recompute_and_consume_failures(client, case):
    evidence = ingest(client, case, ssh("04:45:00", "Failed") + ssh("04:45:01", "Failed"), "Host")
    ingest(client, case, ssh("04:43:00", "Accepted") + ssh("04:43:03", "Accepted"), "Host")
    assert not review(client, case, "authentication_sequence")
    endpoint = f"/api/investigations/{case}/evidence/{evidence['id']}/clock"
    assert client.patch(endpoint, json={"offset_seconds": -180, "uncertainty_seconds": 0, "reason": "Measured offset"}).is_success
    lead, = review(client, case, "authentication_sequence")
    assert lead["start"].endswith("04:42:01.000000Z")
    assert [ref["line_number"] for ref in lead["references"]] == [2, 1]


@pytest.mark.parametrize("clock,source,ip,expected", [
    ("04:50:00", "Host", IP, 1), ("04:50:01", "Host", IP, 0),
    ("04:41:00", "Web", IP, 0), ("04:41:00", "Host", "192.0.2.1", 0)])
def test_group_cross_source(client, case, clock, source, ip, expected):
    ingest(client, case, web("04:40:00") * 20, "Web")
    ingest(client, case, ssh(clock, "Accepted", ip) * 15, source)
    leads = review(client, case, "cross_source_activity")
    assert len(leads) == expected
    if leads:
        assert len(set(leads[0]["record_ids"])) == 35


def test_sensitive_paths_are_explicit(client, case):
    paths = ["/downloads/backup.tar?version=1", "/.git/config", "/admin/", "/about?file=backup.tar", "/administrator", "/backup.tar.html"]
    ingest(client, case, b"".join(web("04:40:00", path) for path in paths), "Web")
    leads = review(client, case, "sensitive_activity")
    assert sorted(f["references"][0]["line_number"] for f in leads) == [1, 2, 3]


def test_portable_package(client, case, tmp_path):
    prefix = f"/api/investigations/{case}"
    originals = {}
    for name in ["auth.log", "web.log"]:
        data = (ROOT / "datasets/B_cross_source" / name).read_bytes()
        item = ingest(client, case, data, name)
        originals[item["id"]] = data
    extra = ingest(client, case, b"unparsed\xff\r\n", "Unclassified")
    originals[extra["id"]] = b"unparsed\xff\r\n"
    store = client.app.state.store
    with store.connect() as db:
        before = list(db.iterdump())
    response = client.get(prefix + "/case.zip")
    assert response.status_code == 200 and response.headers["content-type"] == "application/zip"
    with store.connect() as db:
        assert before == list(db.iterdump())
    archive = tmp_path / "case.zip"
    archive.write_bytes(response.content)
    with ZipFile(archive) as package:
        report = json.loads(package.read("report.json"))
        assert report["audit"] and len(report["gaps"]) == 1
        assert report["investigation"]["id"] == case and len(report["timeline"]) == 6
        assert {lead["title"] for lead in report["findings"]} == {
            "Backup archive requested", "Privileged command recorded", "Administrative endpoint requested",
            "Authentication sequence requiring review", "Related activity across multiple sources"}
        for entry in json.loads(package.read("manifest.json"))["files"]:
            contents = package.read(entry["path"])
            assert hashlib.sha256(contents).hexdigest() == entry["sha256"]
            if "evidence_id" in entry:
                assert contents == originals[entry["evidence_id"]] and entry["filename"] == "events.log"
        members = {name: package.read(name) for name in package.namelist()}
    def run_verifier():
        return subprocess.run([sys.executable, str(ROOT / "scripts/verify_case.py"), str(archive)], capture_output=True)
    assert run_verifier().returncode == 0
    for mode in ["alter", "omit"]:
        with ZipFile(archive, "w") as broken:
            for name, data in members.items():
                if name == "report.json" and mode == "omit":
                    continue
                broken.writestr(name, b"changed" if name.startswith("evidence/") else data)
        result = run_verifier()
        assert result.returncode and b"FAIL" in result.stderr
    path = store.vault / extra["id"]
    path.chmod(0o666)
    path.write_bytes(b"damaged")
    assert client.get(prefix + "/case.zip").status_code == 409
    path.unlink()
    assert client.get(prefix + "/case.zip").status_code == 409
