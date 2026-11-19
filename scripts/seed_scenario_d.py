"""Import Scenario D into a fresh, clearly named investigation on the local API."""
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx

DATA = Path(__file__).resolve().parents[1] / "datasets/D_realistic_incident"


def seed(client):
    spec = json.loads((DATA/"ground_truth.json").read_text(encoding="utf-8-sig"))
    for file in spec["files"]:
        if not (DATA/file["filename"]).is_file():
            raise FileNotFoundError(file["filename"])
    cases = client.get("/api/investigations")
    cases.raise_for_status()
    name = spec["name"]
    if any(case["name"] == name for case in cases.json()):
        name += " / " + datetime.now(timezone.utc).strftime("%H%M%S.%f UTC")
    created = client.post("/api/investigations", json={"name": name, "description": spec["description"]})
    created.raise_for_status()
    investigation = created.json()
    prefix = "/api/investigations/" + investigation["id"]
    print("Created", name, investigation["id"], flush=True)
    for settings in spec["files"]:
        filename = settings["filename"]
        response = client.post(prefix + "/evidence", files={"file": (filename, (DATA/filename).read_bytes())},
                               data={"options": json.dumps({k:v for k,v in settings.items() if k != "filename"})})
        response.raise_for_status()
    return investigation


if __name__ == "__main__":
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30) as local:
        seed(local)
