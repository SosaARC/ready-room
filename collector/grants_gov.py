"""Grants.gov: every posted and forecasted federal grant, tagged with who may apply.

Uses the public search2 API (POST https://api.grants.gov/v1/api/search2, no key).
search2 returns ids, titles, agencies and dates, but not eligibility, so we run one
search per applicant group and record which groups each opportunity appeared under.
"""
import re

import html

from .common import MECHANISM, NOT_FUNDING, RESEARCH_AGENCY, http, mdy_to_iso, record, state_in_title, tag_text

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
AGENCY_NAMES = {"HHS": "Department of Health and Human Services", "NIH": "National Institutes of Health", "NSF": "National Science Foundation",
    "DOT": "Department of Transportation", "USDA": "Department of Agriculture", "DOE": "Department of Energy", "EPA": "Environmental Protection Agency",
    "DOJ": "Department of Justice", "ED": "Department of Education", "DOL": "Department of Labor", "HUD": "Department of Housing and Urban Development",
    "DOC": "Department of Commerce", "SBA": "Small Business Administration", "NEA": "National Endowment for the Arts", "NEH": "National Endowment for the Humanities",
    "IMLS": "Institute of Museum and Library Services", "DOI": "Department of the Interior", "DHS": "Department of Homeland Security", "VA": "Department of Veterans Affairs",
    "DOD": "Department of Defense", "DOS": "Department of State", "USAID": "U.S. Agency for International Development", "NASA": "NASA", "CNCS": "AmeriCorps"}


def agency_name(name, code):
    """Grants.gov sometimes returns only a code like HHS-NIH11. Turn it into a readable name."""
    if name and not __import__("re").fullmatch(r"[A-Z0-9-]+", name.strip()):
        return name.strip()
    c = (code or name or "").upper()
    parts = [p for p in __import__("re").split(r"[-\d]+", c) if p]
    names = [AGENCY_NAMES[p] for p in parts if p in AGENCY_NAMES]
    if not names:
        return code or name or "Federal agency"
    return names[-1] if len(names) > 1 and names[0].startswith("Department of Health") else names[0]


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
                    title = re.sub(r"[\u200b\ufeff]", "", html.unescape(h.get("title") or "")).strip()
                    only_state = state_in_title(title)
                    agency = agency_name(h.get("agencyName") or h.get("agency") or "", h.get("agencyCode", ""))
                    focus = tag_text(title, agency, h.get("agencyCode", ""))
                    research_only = bool(re.search(MECHANISM, title, re.I)) or bool(re.search(RESEARCH_AGENCY, f"{agency} {h.get('agencyCode', '')}")) or ("research" in focus and not any(t in focus for t in ("small-business", "transportation", "workforce", "community-development")))
                    close = mdy_to_iso(h.get("closeDate"))
                    rec = record(
                        id=f"gg-{oid}", source="grants.gov", source_id=oid,
                        name=title, funder=agency,
                        level="federal", region=only_state or "US", type="notice" if re.search(NOT_FUNDING, title, re.I) else "grant",
                        focus=focus, must_have_any=["research"] if research_only else [],
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
