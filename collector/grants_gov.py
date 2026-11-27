"""Grants.gov: every posted and forecasted federal grant, tagged with who may apply.

Uses the public search2 API (POST https://api.grants.gov/v1/api/search2, no key).
search2 returns ids, titles, agencies and dates, but not eligibility, so we run one
search per applicant group and record which groups each opportunity appeared under.
"""
from .common import http, mdy_to_iso, record

API = "https://api.grants.gov/v1/api/search2"

# Grants.gov eligibility codes grouped the way Ready Room screens applicants.
GROUPS = {
    "for-profit": ["23", "22"],            # small businesses; for-profits other than small businesses
    "nonprofit": ["12", "13"],             # nonprofits with and without 501(c)(3), other than higher ed
    "individual": ["21"],
    "government": ["00", "01", "02", "04", "05", "08"],
    "tribal": ["07", "11"],
    "any": ["99"],                          # unrestricted
}
PAGE = 250
MAX_PER_GROUP = 3000


def search(codes, start=0, fetch=http):
    return fetch(API, {
        "rows": PAGE, "startRecordNum": start, "keyword": "",
        "oppStatuses": "forecasted|posted", "eligibilities": "|".join(codes),
    })


def collect(fetch=http, log=print):
    seen = {}
    for group, codes in GROUPS.items():
        start, total = 0, None
        while True:
            payload = search(codes, start, fetch)
            if payload.get("errorcode") not in (0, None):
                raise RuntimeError(f"Grants.gov error: {payload.get('msg')}")
            data = payload.get("data") or {}
            hits = data.get("oppHits") or []
            total = data.get("hitCount", len(hits)) if total is None else total
            for h in hits:
                oid = str(h.get("id", ""))
                if not oid:
                    continue
                rec = seen.get(oid)
                if rec is None:
                    status = h.get("oppStatus", "")
                    close = mdy_to_iso(h.get("closeDate"))
                    rec = record(
                        id=f"gg-{oid}", source="grants.gov", source_id=oid,
                        name=h.get("title", "").strip(), funder=h.get("agencyName") or h.get("agencyCode", ""),
                        level="federal", region="US", type="grant",
                        deadline=close,
                        deadline_text="Forecasted; dates not set yet" if status == "forecasted" else ("" if close else "See notice"),
                        url=f"https://www.grants.gov/search-results-detail/{oid}",
                        documents_typically_needed=["DUNS/UEI + SAM registration", "budget"],
                        notes=f"Grants.gov {h.get('number', '')}. Assistance listing {', '.join(h.get('alnist') or [])}.".strip(),
                        requirements=["Active SAM.gov registration (UEI) required to apply"],
                        eligible_entities=[],
                    )
                    rec["_groups"] = set()
                    seen[oid] = rec
                rec["_groups"].add(group)
            start += PAGE
            if not hits or start >= min(total or 0, MAX_PER_GROUP):
                break
        log(f"grants.gov: {group}: {total} matches")
    out = []
    for rec in seen.values():
        g = rec.pop("_groups")
        ents = ["for-profit", "nonprofit", "individual", "government", "tribal"] if "any" in g else sorted(g)
        rec["eligible_entities"] = ents
        out.append(rec)
    return out
