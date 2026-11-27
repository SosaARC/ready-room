#!/usr/bin/env python3
"""Build dist/index.html from src/app.html plus the grant catalog in data/.

Usage: python3 build.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).parent


def as_script_json(value):
    # JSON inside a <script> tag: escape "<" so the data can never close the tag.
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


def main():
    src = (ROOT / "src" / "app.html").read_text(encoding="utf-8")
    grants = json.loads((ROOT / "data" / "grants.json").read_text(encoding="utf-8"))
    not_grants_path = ROOT / "data" / "not-grants.json"
    not_grants = json.loads(not_grants_path.read_text(encoding="utf-8")) if not_grants_path.exists() else []
    live_p = ROOT / "data" / "live" / "opportunities.json"
    live = [g for g in json.loads(live_p.read_text(encoding="utf-8")) if g.get("type") != "program"] if live_p.exists() else []
    status_p = ROOT / "data" / "live" / "status.json"
    live_status = json.loads(status_p.read_text(encoding="utf-8")) if status_p.exists() else {}
    dates = sorted({g.get("verified_on") for g in grants if g.get("verified_on")})
    catalog_date = dates[-1] if dates else ""
    out = (
        src.replace("__GRANTS__", as_script_json(grants))
        .replace("__NOTGRANTS__", as_script_json(not_grants))
        .replace("__LIVE__", as_script_json(live))
        .replace("__LIVESTATUS__", as_script_json({k: live_status.get(k) for k in ("run_at", "total", "new")}))
        .replace("__CATALOG_DATE__", catalog_date)
    )
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    (dist / "index.html").write_text(out, encoding="utf-8")
    print(f"Built dist/index.html with {len(grants)} curated programs, {len(live)} collected opportunities and {len(not_grants)} warnings (catalog date {catalog_date}).")


if __name__ == "__main__":
    main()
