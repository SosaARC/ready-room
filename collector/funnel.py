"""The funnel: from every opportunity to the few worth applying for now.

    python -m collector.funnel path/to/business-backup.json [--top 15] [--md report.md]

The business file is a Ready Room backup or starter file. Stages:
  1. Can you apply?    Hard rules: entity type, place, restricted groups, excluded types, age, size, loans.
  2. Should you?       Fit: focus areas, industry, documents already on file.
  3. Can you win it in time?
       Timeline:     days to deadline vs. days this business needs to prepare
       Credentials:  SAM.gov/UEI for federal, 501(c)(3) letters, certifications
       Competition:  local and state programs beat national lotteries; more awards is better
Result: Apply now, Prepare for the next round, or Skip, each with reasons.
This mirrors the rules in the app (src/app.html, assess() and funnel()).
"""
import argparse
import datetime as dt
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TODAY = dt.date.today()
TRIAD = {"alamance", "caswell", "davidson", "davie", "forsyth", "guilford", "montgomery", "randolph", "rockingham", "stokes", "surry", "yadkin"}
ENTITY_CLASS = {"llc": "for-profit", "corp": "for-profit", "sole": "for-profit", "partnership": "for-profit",
                "np501c3": "nonprofit", "np_pending": "nonprofit", "np_other": "nonprofit", "gov": "government"}
DOC_MAP = {"business plan": "business_plan", "financial statements": "financials", "tax returns": "tax_returns", "budget": "budget",
           "articles of incorporation": "articles", "501c3 letter": "irs_501c3", "w-9": "w9", "certificate of good standing": "good_standing",
           "capability statement": "capability", "letters of support": "support_letters", "hub certification": "hub_cert",
           "duns/uei + sam registration": "sam_uei"}
BROAD_TAGS = {"education", "justice", "disaster", "health", "community-development", "environment", "rural", "energy", "research", "low-income", "economic-mobility"}
RECUR = re.compile(r"monthly|rolling|annual|twice a year|each year|quarterly|ongoing", re.I)
DOC_LABEL = {"business_plan": "a business plan", "financials": "financial statements", "tax_returns": "tax returns", "budget": "a project budget", "articles": "articles of organization", "irs_501c3": "a 501(c)(3) letter (or a fiscal sponsor)", "w9": "a W-9", "good_standing": "a certificate of good standing", "capability": "a capability statement", "support_letters": "letters of support", "hub_cert": "a small business certification", "sam_uei": "a SAM.gov registration"}
EXPIRING = {"coi", "ucr", "mcs150", "med_card", "license", "registration", "dot_inspection", "good_standing", "business_license", "hub_cert", "sam_uei"}


def days_until(s):
    try:
        return (dt.date.fromisoformat(str(s)[:10]) - TODAY).days
    except (TypeError, ValueError):
        return None


def norm_county(c):
    c = str(c or "").lower()
    c = re.sub(r"county|,?\s*(nc|north carolina)\b", "", c)
    return re.sub(r"[^a-z\s-]", "", c).strip()


def has_doc(b, key):
    docs = [d for d in b.get("documents", []) if d.get("type") == key]
    if not docs:
        return False
    best = max(docs, key=lambda d: d.get("expires") or "9999")
    n = days_until(best.get("expires"))
    return n is None or n >= 0


def tags(p):
    t = set(p.get("focus") or [])
    if p.get("founded") and str(p["founded"]).isdigit() and int(p["founded"]) >= TODAY.year - 3:
        t.add("startup")
    if "veteran" in t:
        t.add("military-spouse")
    ind = str(p.get("industry") or "").lower()
    if re.search(r"truck|freight|logist|courier|transport|haul", ind):
        t |= {"transportation", "local-service", "trucking"}
    if re.search(r"farm|agri", ind):
        t.add("agriculture")
    if re.search(r"software|saas|\bai\b|tech", ind) or "research" in t:
        t.add("tech")
    if "youth-education" in t:
        t.add("education")
    return t


def budget_of(p):
    """Annual budget or revenue as a number, from text like '$420,000', 'Under $100K' or '1.2M'."""
    for k in ("budget", "revenue"):
        m = re.search(r"\$?\s*([\d,.]+)\s*([kKmM])?", str(p.get(k) or ""))
        if m:
            try:
                n = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            n *= {"k": 1e3, "m": 1e6}.get((m.group(2) or "").lower(), 1)
            if n >= 1000:
                return n
    return None


def screen(g, b):
    """Stage 1. Returns (ok, reasons_for, reasons_against, notes)."""
    p = b["profile"]
    ent = ENTITY_CLASS.get(p.get("entityType"), "for-profit")
    yes, no, notes = [], [], []
    el = g.get("eligible_entities") or []
    if el and ent not in el and not (ent == "for-profit" and "individual" in el):
        no.append({"for-profit": "Nonprofits or governments only", "nonprofit": "Not open to nonprofits"}.get(ent, "Not open to this applicant type"))
    elif el:
        yes.append(f"Open to {ent} applicants")
    reg = str(g.get("region") or "").lower()
    county, city, st = norm_county(p.get("county")), str(p.get("city") or "").lower().strip(), str(p.get("state") or "").upper().strip()
    if g.get("level") == "local":
        wb = lambda w: re.search(r"\b" + re.escape(w) + r"\b", reg)  # noqa: E731
        reg_no_counties = re.sub(r"\b[a-z]+(?:,\s*[a-z]+)*\s+count(y|ies)\b", "", reg)
        if (county and wb(county)) or (city and re.search(r"\b" + re.escape(city) + r"\b", reg_no_counties)):
            yes.append("Local to you")
        else:
            no.append(f"Outside your area ({g.get('region')})")
    elif g.get("level") == "state" and ("north carolina" in reg or re.search(r"\bnc\b", reg)) and st not in ("NC", "NORTH CAROLINA"):
        no.append("North Carolina only")
    if g.get("area_check"):
        notes.append("Only part of the area qualifies: check the address")
    t = tags(p)
    must = g.get("must_have_any") or []
    if must and not any(m in t for m in must):
        no.append("Only for: " + " or ".join(must))
    exc = [m for m in (g.get("excludes_any") or []) if m in t]
    if exc:
        no.append("Excludes: " + ", ".join(exc))
    if g.get("min_years"):
        if p.get("founded") and str(p["founded"]).isdigit():
            if TODAY.year - int(p["founded"]) < g["min_years"]:
                no.append(f"Business must be {g['min_years']}+ years old")
        else:
            notes.append("Needs years in business: add founding year")
    if g.get("employees_range") and str(p.get("employees") or "").isdigit():
        lo, hi = g["employees_range"]
        if not lo <= int(p["employees"]) <= hi:
            no.append(f"Needs {lo} to {hi} workers")
    if g.get("is_loan"):
        no.append("A loan, not a grant")
    if p.get("entityType") == "np_other" and "for-profit" not in el and any(d.lower() == "501c3 letter" for d in g.get("documents_typically_needed") or []):
        no.append("501(c)(3) organizations only")
    dd = days_until(g.get("deadline"))
    if dd is not None and dd < 0 and not RECUR.search(g.get("deadline_text") or ""):
        no.append("Closed")
    return (not no), yes, no, notes


def fit(g, b):
    """Stage 2. 0 to 100."""
    t = tags(b["profile"])
    hits = [f for f in (g.get("focus") or []) if f in t and f not in ("local-service",)]
    s = 45 + min(30, 12 * len(set(hits)))
    if "general" in (g.get("focus") or []):
        s += 5
    s += {"local": 12, "state": 8}.get(g.get("level"), 0)
    docs = [DOC_MAP.get(d.lower()) for d in g.get("documents_typically_needed") or []]
    docs = [d for d in docs if d]
    if docs:
        s += round(10 * sum(has_doc(b, d) for d in docs) / len(docs))
    return min(100, s), sorted(set(hits))


def prep_days(g, b):
    """How long this business needs before it can submit."""
    level, typ = g.get("level"), g.get("type", "grant")
    base = {"federal": 21, "state": 14, "local": 10, "national-private": 4}.get(level, 10)
    if typ == "contract":
        base = 10
    need = []
    docs = [DOC_MAP.get(d.lower()) for d in g.get("documents_typically_needed") or []]
    missing = [d for d in docs if d and not has_doc(b, d)]
    if level == "federal" and not has_doc(b, "sam_uei") and not b["profile"].get("uei"):
        base += 28
        need.append("Register in SAM.gov and get a UEI (allow several weeks)")
    base += 3 * len([m for m in missing if m != "sam_uei"])
    need += [f"Get {DOC_LABEL.get(m, m)}" for m in missing if m != "sam_uei"]
    if g.get("cost_share"):
        base += 5
        need.append("Plan your match: this program requires cost share")
    answers = b.get("answers") or {}
    if sum(1 for v in answers.values() if len(str(v).strip()) > 40) < 4 and typ != "contract":
        base += 5
        need.append("Write the core answers (need, use of funds, impact)")
    return base, need


def odds(g, b=None):
    level, n = g.get("level"), g.get("expected_awards")
    size = budget_of(b["profile"]) if b else None
    if size and g.get("amount_min") and g["amount_min"] > 2 * size:
        return "Long shot", "the smallest award is more than twice your annual budget"
    if level == "national-private":
        return "Long shot", "National program with many applicants per award"
    if isinstance(n, (int, float)) and n and n <= 3:
        return "Long shot", f"Only {int(n)} award(s) expected"
    if level in ("local", "state"):
        return "Better", "Local or state pool: fewer applicants"
    return "Fair", "Competitive national pool"


def funnel(g, b):
    ok, yes, no, notes = screen(g, b)
    if not ok:
        return {"bucket": "Skip", "why": no, "score": 0}
    if g.get("type") == "program":
        return {"bucket": "Skip", "why": ["Program listing, not an open call: watch for its next notice"], "score": 0}
    if g.get("type") == "notice":
        return {"bucket": "Skip", "why": ["Notice or request for information, not a funding call"], "score": 0}
    score, hits = fit(g, b)
    if g.get("source", "curated") not in ("curated", ""):
        reg = str(g.get("region") or "US")
        st = str(b["profile"].get("state") or "").upper()
        if reg != "US" and g.get("level") == "federal" and g.get("type") != "contract":
            from .common import US_STATES
            if reg in US_STATES and not (st in ("NC", "NORTH CAROLINA") and reg == "North Carolina"):
                return {"bucket": "Skip", "why": [f"For {reg} only"], "score": 0}
        if not hits:
            return {"bucket": "Skip", "why": ["No match to your focus areas"], "score": 0}
        if len(hits) < 2 and hits[0] in BROAD_TAGS and g.get("type") != "contract":
            return {"bucket": "Skip", "why": [f"Weak match (only {hits[0]})"], "score": 0}
    need_days, need = prep_days(g, b)
    dd = days_until(g.get("deadline"))
    recur = bool(RECUR.search(g.get("deadline_text") or "")) or g.get("deadline") is None
    od, od_why = odds(g, b)
    why = yes + ([f"Matches {', '.join(hits)}"] if hits else []) + notes + [f"Odds: {od.lower()} ({od_why})"]
    if score < 50:
        return {"bucket": "Skip", "why": [f"Weak fit (score {score})"] + why, "score": score}
    if dd is not None and dd < need_days:
        if recur:
            first = (f"Last round closed {g.get('deadline')}. Get ready for the next one (about {need_days} days of prep)." if dd < 0
                     else f"Due in {dd} days, but you need about {need_days}. Get ready for the next round.")
            return {"bucket": "Prepare", "why": [first] + need + why, "score": score}
        return {"bucket": "Skip", "why": [f"Not enough time: due in {dd} days, about {need_days} days of prep needed"] + need, "score": score}
    unknown = [n for n in notes if n.startswith("Needs")]
    if (need and any("SAM.gov" in n for n in need)) or unknown:
        return {"bucket": "Prepare", "why": unknown + need + why, "score": score}
    rank = score + (10 if od == "Better" else -10 if od == "Long shot" else 0) + (5 if dd is not None and dd <= 45 else 0)
    return {"bucket": "Apply now", "why": [f"Due in {dd} days" if dd is not None else "Open or rolling"] + need + why, "score": rank}


def load_all():
    cur = json.loads((ROOT / "data" / "grants.json").read_text(encoding="utf-8"))
    live_p = ROOT / "data" / "live" / "opportunities.json"
    live = json.loads(live_p.read_text(encoding="utf-8")) if live_p.exists() else []
    for g in cur:
        g.setdefault("source", "curated")
        g.setdefault("type", "grant")
    return cur + live


def run(biz, opps, top=15):
    res = {"Apply now": [], "Prepare": [], "Skip": []}
    skip_reasons = {}
    for g in opps:
        f = funnel(g, biz)
        res[f["bucket"]].append((g, f))
        if f["bucket"] == "Skip":
            key = f["why"][0].split(":")[0].split("(")[0].strip()
            skip_reasons[key] = skip_reasons.get(key, 0) + 1
    for k in res:
        res[k].sort(key=lambda x: -x[1]["score"])
    return res, skip_reasons


def markdown(biz, opps, res, skip_reasons, top=15):
    p = biz["profile"]
    L = [f"# Funnel for {p.get('name')}, {TODAY.isoformat()}", "",
         f"Checked **{len(opps)}** opportunities: **{len(res['Apply now'])}** apply now, **{len(res['Prepare'])}** prepare for, **{len(res['Skip'])}** skipped.", ""]
    for b, title in (("Apply now", "Apply now"), ("Prepare", "Prepare for the next round")):
        L += [f"## {title}", ""]
        if not res[b]:
            L += ["None right now.", ""]
        for g, f in res[b][:top]:
            L.append(f"- **{g['name']}** ({g.get('funder', '')}, {g.get('type', 'grant')}) [{g.get('source', '')}]({g.get('url', '')})")
            L += [f"  - {w}" for w in f["why"][:5]]
        L.append("")
    L += ["## Why the rest were skipped", "", "| Reason | Count |", "| --- | ---: |"]
    L += [f"| {k} | {v} |" for k, v in sorted(skip_reasons.items(), key=lambda x: -x[1])[:12]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("business")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--md")
    a = ap.parse_args(argv)
    biz = json.loads(pathlib.Path(a.business).read_text(encoding="utf-8"))
    opps = load_all()
    res, skip = run(biz, opps, a.top)
    md = markdown(biz, opps, res, skip, a.top)
    if a.md:
        pathlib.Path(a.md).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
