"""Run every source, merge with the last run, and write data/live/.

    python -m collector.run              # all sources
    python -m collector.run --no-pages   # skip the page watcher (faster)

Writes:
    data/live/opportunities.json   one list, every source, same schema as data/grants.json
    data/live/status.json          per-source counts, errors, run time
    data/live/page-hashes.json     fingerprints of curated official pages
    data/live/REPORT.md            what is new, closing soon, and which curated pages changed
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

from . import grants_gov, page_watch, sam_gov, sbir
from .common import TODAY

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = ROOT / "data" / "live"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def run(sources, do_pages=True, log=print):
    LIVE.mkdir(parents=True, exist_ok=True)
    previous = {r["id"]: r for r in load(LIVE / "opportunities.json", [])}
    status = {"run_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "sources": {}}
    fresh = {}
    for name, fn in sources.items():
        try:
            recs = fn(log=log)
        except Exception as e:  # noqa: BLE001 - one bad source must not stop the run
            log(f"{name}: FAILED {e}")
            status["sources"][name] = {"ok": False, "error": str(e)[:200]}
            recs = None
        if recs is None:  # unavailable: keep last run's records for this source
            kept = [r for r in previous.values() if r.get("source") == name]
            for r in kept:
                fresh[r["id"]] = r
            status["sources"].setdefault(name, {"ok": False, "error": "unavailable", "kept_from_last_run": len(kept)})
            continue
        status["sources"][name] = {"ok": True, "count": len(recs)}
        for r in recs:
            old = previous.get(r["id"])
            if old:
                r["first_seen"] = old.get("first_seen", TODAY)
            fresh[r["id"]] = r
    new = [r for r in fresh.values() if r["id"] not in previous]
    gone = [r for r in previous.values() if r["id"] not in fresh]
    out = sorted(fresh.values(), key=lambda r: (r.get("deadline") or "9999", r["name"]))
    (LIVE / "opportunities.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    changed, failed = [], []
    if do_pages:
        catalog = load(ROOT / "data" / "grants.json", [])
        hashes, changed, failed = page_watch.check(catalog, load(LIVE / "page-hashes.json", {}), log=log)
        (LIVE / "page-hashes.json").write_text(json.dumps(hashes, indent=1, sort_keys=True), encoding="utf-8")
    status.update(total=len(out), new=len(new), removed=len(gone), pages_changed=len(changed), pages_unchecked=len(failed))
    (LIVE / "status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")
    (LIVE / "REPORT.md").write_text(report(out, new, gone, changed, failed, status), encoding="utf-8")
    log(f"done: {len(out)} opportunities, {len(new)} new, {len(gone)} removed")
    return out, status


def report(out, new, gone, changed, failed, status):
    soon = [r for r in out if r.get("deadline") and TODAY <= r["deadline"] <= (dt.date.today() + dt.timedelta(days=21)).isoformat()]
    by_src = {}
    for r in out:
        by_src[r["source"]] = by_src.get(r["source"], 0) + 1
    L = [f"# Collector report, {TODAY}", "", "| Source | Records | Status |", "| --- | ---: | --- |"]
    for name, st in status["sources"].items():
        L.append(f"| {name} | {by_src.get(name, 0)} | {'ok' if st.get('ok') else st.get('error', 'failed')} |")
    L += ["", f"**{len(out)} open opportunities. {len(new)} new since the last run, {len(gone)} closed or removed.**", ""]
    if changed:
        L += ["## Curated pages that changed (re-check these in data/grants.json)", ""]
        L += [f"- [{name}]({url}) (`{gid}`)" for gid, name, url in changed] + [""]
    if new:
        L += ["## New", ""] + [f"- {r['name']} ({r['funder']}){', due ' + r['deadline'] if r.get('deadline') else ''} [{r['source']}]({r['url']})" for r in new[:80]]
        if len(new) > 80:
            L.append(f"- ...and {len(new) - 80} more")
        L.append("")
    if soon:
        L += ["## Closing in the next 3 weeks", ""] + [f"- {r['deadline']}: {r['name']} ({r['funder']})" for r in soon[:60]] + [""]
    if failed:
        L += ["## Pages the watcher could not check", ""] + [f"- `{gid}`: {why}" for gid, _, why in failed] + [""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pages", action="store_true")
    ap.add_argument("--only", nargs="*", help="grants.gov sbir.gov sam.gov-contracts sam.gov-listings")
    a = ap.parse_args(argv)
    sources = {
        "grants.gov": grants_gov.collect,
        "sbir.gov": sbir.collect,
        "sam.gov contracts": sam_gov.contracts,
        "sam.gov assistance listings": sam_gov.assistance_listings,
    }
    if a.only:
        want = {s.replace("-", " ") for s in a.only}
        sources = {k: v for k, v in sources.items() if k in want or k.split()[0] in want}
    run(sources, do_pages=not a.no_pages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
