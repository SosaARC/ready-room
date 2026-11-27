"""SAM.gov: federal contract opportunities and assistance program listings.

Both need a free public API key (SAM.gov > Account Details > Public API Key), stored
as the SAM_API_KEY secret. A personal key with no SAM.gov role gets about 10 requests
a day, so each run makes one large request per endpoint.

Contract opportunities are not grants, but small set-asides for trucking, courier and
moving work are often a better fit for a small carrier than any federal grant.
"""
import datetime as dt
import os
import urllib.parse

from .common import http, mdy_to_iso, record, redact

OPP_API = "https://api.sam.gov/opportunities/v2/search"
AL_API = "https://api.sam.gov/assistance-listings/v1/search"

# NAICS codes worth watching for transportation, logistics and moving work. Edit freely.
WATCH_NAICS = {
    "484110": "General freight trucking, local",
    "484121": "General freight trucking, long-distance, truckload",
    "484122": "General freight trucking, long-distance, less than truckload",
    "484210": "Used household and office goods moving",
    "484220": "Specialized freight trucking, local",
    "492110": "Couriers and express delivery",
    "492210": "Local messengers and local delivery",
    "488510": "Freight transportation arrangement",
    "562111": "Solid waste collection",
    "493110": "General warehousing and storage",
}
SET_ASIDE_LABEL = {"SBA": "Small business set-aside", "SBP": "Partial small business set-aside", "8A": "8(a) set-aside",
                   "HZC": "HUBZone set-aside", "WOSB": "Women-owned small business set-aside",
                   "EDWOSB": "Economically disadvantaged WOSB set-aside", "SDVOSBC": "Service-disabled veteran-owned set-aside",
                   "VSA": "Veteran-owned set-aside"}


def key():
    return os.environ.get("SAM_API_KEY", "").strip()


def contracts(states=("NC", "SC", "VA", "GA", "TN"), days=7, fetch=http, log=print):
    k = key()
    if not k:
        log("sam.gov contracts: skipped (no SAM_API_KEY)")
        return []
    to = dt.date.today()
    frm = to - dt.timedelta(days=days)
    q = {"api_key": k, "postedFrom": frm.strftime("%m/%d/%Y"), "postedTo": to.strftime("%m/%d/%Y"),
         "ptype": "o", "limit": 1000, "offset": 0}
    url = OPP_API + "?" + urllib.parse.urlencode(q)
    log("sam.gov contracts: " + redact(url))
    data = fetch(url)
    out = []
    for o in data.get("opportunitiesData") or []:
        naics = str(o.get("naicsCode") or "")
        pop = o.get("placeOfPerformance") or {}
        st = ((pop.get("state") or {}).get("code") or "") if isinstance(pop.get("state"), dict) else str(pop.get("state") or "")
        if naics not in WATCH_NAICS:
            continue
        if states and st and st not in states:
            continue
        aside = o.get("typeOfSetAside") or ""
        musts = {"WOSB": ["women-owned"], "EDWOSB": ["women-owned"], "SDVOSBC": ["veteran"], "VSA": ["veteran"]}.get(aside, [])
        nid = str(o.get("noticeId") or o.get("solicitationNumber") or "")
        city = ((pop.get("city") or {}).get("name") or "") if isinstance(pop.get("city"), dict) else ""
        out.append(record(
            id=f"sam-{nid}", source="sam.gov contracts", source_id=nid, type="contract", kind="contract",
            name=(o.get("title") or "").strip(), funder=o.get("fullParentPathName") or o.get("department") or "Federal agency",
            level="federal", region=", ".join(x for x in (city, st) if x) or "US",
            eligible_entities=["for-profit"], focus=["transportation", "trucking"],
            deadline=mdy_to_iso(o.get("responseDeadLine")), deadline_text="Response due",
            amount_text="Contract value in the notice",
            requirements=[r for r in [SET_ASIDE_LABEL.get(aside, ""), f"NAICS {naics}: {WATCH_NAICS[naics]}",
                                      "Active SAM.gov registration (UEI) required to bid"] if r],
            documents_typically_needed=["DUNS/UEI + SAM registration", "capability statement"],
            must_have_any=musts, url=f"https://sam.gov/opp/{nid}/view" if nid else "",
            notes="Federal contract opportunity, not a grant. Payment is for work performed.",
        ))
    log(f"sam.gov contracts: {len(out)} matching {len(WATCH_NAICS)} watched NAICS codes")
    return out


def assistance_listings(fetch=http, log=print):
    """Active federal grant programs (the old CFDA catalog). One request, up to 1000 listings."""
    k = key()
    if not k:
        log("sam.gov assistance listings: skipped (no SAM_API_KEY)")
        return []
    q = {"api_key": k, "status": "Active", "pageSize": 1000, "pageNumber": 0, "assistanceTypes": "F001"}
    url = AL_API + "?" + urllib.parse.urlencode(q)
    log("sam.gov assistance listings: " + redact(url))
    data = fetch(url)
    out = []
    applicant_map = (("profit", "for-profit"), ("small business", "for-profit"), ("nonprofit", "nonprofit"),
                     ("non-profit", "nonprofit"), ("individual", "individual"), ("tribal", "tribal"),
                     ("state", "government"), ("local", "government"), ("government", "government"))
    for a in data.get("assistanceListingsData") or []:
        alid = a.get("assistanceListingId") or ""
        types = ((a.get("criteriaForApplying") or {}).get("applicant") or {}).get("types") or []
        names = " | ".join(str(t.get("name", "")).lower() for t in types if isinstance(t, dict))
        ents = sorted({v for k2, v in applicant_map if k2 in names})
        rng = ((a.get("financialInformation") or {}).get("rangeAndAverageAssistance") or [])
        out.append(record(
            id=f"al-{alid}", source="sam.gov assistance listings", source_id=alid, type="program",
            name=(a.get("title") or "").strip(), funder=((a.get("federalOrganization") or {}).get("name") or "Federal agency"),
            level="federal", region="US", eligible_entities=ents,
            deadline=None, deadline_text="Program listing: watch Grants.gov for open notices under this number",
            url=a.get("programWebPage") or f"https://sam.gov/fal/{alid}/view",
            notes=f"Assistance listing {alid}. {str((a.get('overview') or {}).get('objective') or '')[:220]}".strip(),
            amount_text="See listing" if not rng else "Range in listing",
        ))
    log(f"sam.gov assistance listings: {len(out)} grant programs")
    return out
