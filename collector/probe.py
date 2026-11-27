"""One-off: save raw Grants.gov fetchOpportunity responses so the parser can be written against real data."""
import json
import pathlib

from .common import http

ids = [r["source_id"] for r in json.loads(pathlib.Path("data/live/opportunities.json").read_text())[:400:130]]
out = {}
for i in ids:
    try:
        out[i] = http("https://api.grants.gov/v1/api/fetchOpportunity", {"opportunityId": int(i)})
    except Exception as e:  # noqa: BLE001
        out[i] = {"error": str(e)}
p = pathlib.Path("data/probe")
p.mkdir(parents=True, exist_ok=True)
(p / "fetchOpportunity.json").write_text(json.dumps(out, indent=1))
print("saved", list(out))
