"""Read each Grants.gov opportunity's full record, not just its title.

The search API gives titles and dates. fetchOpportunity gives the facts that decide
whether a business can win: exactly who may apply (applicantTypes), award floor and
ceiling, number of awards, whether a match is required, topic categories, and the
description. Details are cached in data/live/details-cache.json and only re-fetched
when an opportunity is new, its close date changed, or the cache entry is 14+ days old.
"""
import datetime as dt
import html
import json
import pathlib
import re
import time

from .common import http, tag_text

API = "https://api.grants.gov/v1/api/fetchOpportunity"
CACHE = pathlib.Path(__file__).resolve().parent.parent / "data" / "live" / "details-cache.json"
MAX_FETCH = 1500
REFRESH_DAYS = 14

# Grants.gov applicant type ids -> Ready Room applicant classes.
APPLICANT = {
    "00": "government", "01": "government", "02": "government", "04": "government", "05": "government",
    "06": "government", "08": "government", "07": "tribal", "11": "tribal",
    "12": "nonprofit", "13": "nonprofit", "20": "nonprofit",
    "21": "individual", "22": "for-profit", "23": "for-profit",
}
HIGHER_ED = {"06", "20"}

# Grants.gov funding activity categories -> topic tags.
CATEGORY_TAGS = {
    "T": ["transportation"], "AG": ["agriculture"], "BC": ["small-business"], "CD": ["community-development"],
    "ELT": ["workforce"], "EN": ["energy"], "ENV": ["environment"], "NR": ["environment"], "HL": ["health"],
    "FN": ["health"], "HO": ["community-development"], "RD": ["community-development"], "AR": ["arts"], "HU": ["arts"],
    "ISS": ["low-income"], "ST": ["research"], "ED": ["education"], "LJL": ["justice"], "DPR": ["disaster"],
}


def plain(s, n):
    s = html.unescape(re.sub(r"(?s)<[^>]+>", " ", str(s or "")))
    s = re.sub(r"[​﻿]", "", s)
    return re.sub(r"\s+", " ", s).strip()[:n]


def money(v):
    try:
        x = float(str(v).replace(",", "").replace("$", ""))
        return int(x) if x > 0 else None
    except (TypeError, ValueError):
        return None


def parse(payload):
    """Turn one fetchOpportunity response into the facts the funnel uses."""
    d = (payload or {}).get("data") or {}
    s = d.get("synopsis") or {}
    f = d.get("forecast") or {}
    src = s or f
    types = [t.get("id") for t in (src.get("applicantTypes") or []) if isinstance(t, dict)]
    cats = [c.get("id") for c in (src.get("fundingActivityCategories") or []) if isinstance(c, dict)]
    instruments = [i.get("description") for i in (src.get("fundingInstruments") or []) if isinstance(i, dict)]
    n_awards = src.get("numberOfAwards")
    try:
        n_awards = int(str(n_awards).replace(",", "")) if n_awards not in (None, "", "none") else None
    except ValueError:
        n_awards = None
    resp = src.get("responseDateStr") or f.get("estApplicationResponseDateStr") or ""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", resp)
    return {
        "fetched": dt.date.today().isoformat(),
        "applicant_types": types,
        "ceiling": money(src.get("awardCeiling")),
        "floor": money(src.get("awardFloor")),
        "est_funding": money(src.get("estimatedFunding")),
        "awards": n_awards,
        "cost_share": bool(src.get("costSharing")),
        "categories": cats,
        "instruments": instruments,
        "desc": plain(s.get("synopsisDesc") or f.get("forecastDesc"), 600),
        "elig_desc": plain(src.get("applicantEligibilityDesc"), 300),
        "response_date": m.group(1) if m else None,
        "forecast": bool(f) and not s,
        "updated": src.get("lastUpdatedDate") or "",
    }


RESEARCH_TEXT = re.compile(r"investigator.initiated|research proposals|research projects? (that|to)|rigorous(ly)? evaluat|gold standard research|clinical trials?\b|research and development of", re.I)
SUPPLEMENT_TITLE = re.compile(r"\bsupplement(al|s)?\b|\bcontinuation\b|\bnon-?competing\b", re.I)
SUPPLEMENT_TEXT = re.compile(r"supplemental funding|current(ly funded)? (recipients|grantees|award recipients)|existing (recipients|grantees)|only (current|existing) .{0,40}(recipients|grantees)|limited to (current|existing)", re.I)
HIGHER_ED_TITLE = re.compile(r"\buniversit(y|ies)\b|\bcolleges?\b|\bgraduate\b|\bfellowships?\b|\binternships?\b", re.I)
HIGHER_ED_TEXT = re.compile(r"graduate.level|health professions? (students|schools)|schools of (medicine|nursing|public health)|institutions of higher education only|limited to institutions of higher education", re.I)


def apply(rec, det):
    """Overwrite a collected record's guesses with the facts from its full record."""
    if not det:
        return rec
    types = det.get("applicant_types") or []
    ents = sorted({APPLICANT[t] for t in types if t in APPLICANT})
    if "99" in types:
        ents = ["for-profit", "government", "individual", "nonprofit", "tribal"]
    if ents:
        rec["eligible_entities"] = ents
    if types and set(types) <= HIGHER_ED | {"25"} and "nonprofit" in ents:
        rec.setdefault("requirements", []).append("Institutions of higher education only")
        rec["must_have_any"] = sorted(set(rec.get("must_have_any") or []) | {"higher-ed"})
    if det.get("ceiling"):
        rec["amount_max"] = det["ceiling"]
    if det.get("floor"):
        rec["amount_min"] = det["floor"]
    lo, hi = det.get("floor"), det.get("ceiling")
    if hi and lo:
        rec["amount_text"] = f"${lo:,} to ${hi:,}"
    elif hi:
        rec["amount_text"] = f"Up to ${hi:,}"
    elif det.get("est_funding"):
        rec["amount_text"] = f"${det['est_funding']:,} total"
    rec["expected_awards"] = det.get("awards")
    if det.get("cost_share"):
        reqs = rec.setdefault("requirements", [])
        if "Cost share or match required" not in reqs:
            reqs.append("Cost share or match required")
        rec["cost_share"] = True
    if det.get("response_date") and not rec.get("deadline"):
        rec["deadline"] = det["response_date"]
        if det.get("forecast"):
            rec["deadline_text"] = "Forecast: expected due date"
    cat_tags = [t for c in det.get("categories") or [] for t in CATEGORY_TAGS.get(c, [])]
    title_tags = [t for t in rec.get("focus") or [] if t != "other"]
    desc_tags = [t for t in tag_text(det.get("desc", "")[:300]) if t in ("trucking", "small-business", "veteran", "women-owned")]
    rec["focus"] = sorted(set(title_tags + cat_tags + desc_tags)) or ["other"]
    rec["about"] = det.get("desc", "")[:400]
    title, desc, elig = rec.get("name", ""), det.get("desc", ""), det.get("elig_desc", "") or ""
    musts = set(rec.get("must_have_any") or [])
    reqs = rec.setdefault("requirements", [])
    if RESEARCH_TEXT.search(desc[:1500]):
        musts.add("research")
        if "Research proposals: needs a research team" not in reqs:
            reqs.append("Research proposals: needs a research team")
    if SUPPLEMENT_TITLE.search(title) or SUPPLEMENT_TEXT.search(desc[:1500] + " " + elig):
        musts.add("current-grantee")
        if "Only for organizations this program already funds" not in reqs:
            reqs.append("Only for organizations this program already funds")
    if HIGHER_ED_TITLE.search(title) or HIGHER_ED_TEXT.search(desc[:1500] + " " + elig):
        musts.add("higher-ed")
    if musts:
        rec["must_have_any"] = sorted(musts)
    if det.get("elig_desc"):
        rec["notes"] = (rec.get("notes", "") + " Eligibility: " + det["elig_desc"][:200]).strip()
    if any("loan" in (i or "").lower() for i in det.get("instruments") or []) and not any("grant" in (i or "").lower() for i in det.get("instruments") or []):
        rec["is_loan"] = True
    return rec


def enrich(records, fetch=http, log=print, cache_path=None, max_fetch=MAX_FETCH, pause=0.15):
    cache_path = pathlib.Path(cache_path or CACHE)
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {}
    today = dt.date.today()
    todo = []
    for r in records:
        if r.get("source") != "grants.gov":
            continue
        c = cache.get(r["source_id"])
        stale = not c or c.get("_deadline") != r.get("deadline") or (today - dt.date.fromisoformat(c.get("fetched", "2000-01-01"))).days >= REFRESH_DAYS
        if stale:
            todo.append(r)
    fetched = failed = 0
    for r in todo[:max_fetch]:
        try:
            det = parse(fetch(API, {"opportunityId": int(r["source_id"])}))
            det["_deadline"] = r.get("deadline")
            cache[r["source_id"]] = det
            fetched += 1
        except Exception:  # noqa: BLE001 - one failure shouldn't stop the batch
            failed += 1
        if pause:
            time.sleep(pause)
    live_ids = {r["source_id"] for r in records if r.get("source") == "grants.gov"}
    cache = {k: v for k, v in cache.items() if k in live_ids}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, separators=(",", ":")), encoding="utf-8")
    for r in records:
        if r.get("source") == "grants.gov":
            apply(r, cache.get(r["source_id"]))
    log(f"grants.gov details: {fetched} fetched, {failed} failed, {len(todo) - fetched - failed} left for next run, {len(cache)} cached")
    return records
