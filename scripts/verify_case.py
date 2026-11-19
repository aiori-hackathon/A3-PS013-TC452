"""Independently verify an ALIBI case archive without extracting any entries."""
import argparse
import hashlib
import json
import sys
from uuid import UUID
from zipfile import ZipFile


def verify(path):
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate ZIP entry")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest["format"] != "alibi-case-v1" or manifest["algorithm"] != "SHA-256":
            raise ValueError("unsupported manifest")
        report = json.loads(archive.read("report.json"))
        if report["investigation"]["id"] != manifest["investigation_id"]:
            raise ValueError("investigation mismatch")
        expected = {"report.json", "VERIFY.txt", "verify_case.py"}
        originals = {}
        for evidence in report["evidence"]:
            key = "evidence/" + str(UUID(evidence["id"]))
            if key in originals:
                raise ValueError("duplicate evidence ID")
            originals[key] = evidence
        expected.update(originals)
        entries = manifest["files"]
        if (set(names) != expected | {"manifest.json"} or len(entries) != len(expected)
                or {entry["path"] for entry in entries} != expected):
            raise ValueError("missing, duplicate or unexpected package member")
        for entry in entries:
            name = entry["path"]
            digest = hashlib.sha256()
            with archive.open(name) as member:
                for chunk in iter(lambda: member.read(65536), b""):
                    digest.update(chunk)
            if digest.hexdigest() != entry["sha256"] or archive.getinfo(name).file_size != entry["size"]:
                raise ValueError(f"hash or size mismatch for {name}")
            if name in originals:
                evidence = originals[name]
                if (any(entry[k] != evidence[k] for k in ("filename", "source", "size", "sha256"))
                        or entry["evidence_id"] != evidence["id"]):
                    raise ValueError(f"evidence metadata mismatch for {name}")
        return len(originals)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    try:
        count = verify(parser.parse_args().archive)
    except Exception as error:
        sys.exit(f"FAIL: {error}")
    print(f"PASS: all artifacts verified, including {count} original evidence files.")
