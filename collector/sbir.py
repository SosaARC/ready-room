"""SBIR.gov: open SBIR/STTR solicitations (federal R&D funding for small businesses).

Public API, no key. SBIR.gov has flagged this API as under maintenance at times, so a
failure here is logged and the run continues with the other sources.
"""
from .common import http, mdy_to_iso, record, slug

API = "https://api.www.sbir.gov/public/api/solicitations?open=1&rows=200"


def collect(fetch=http, log=print):
    try:
        data = fetch(API)
    except Exception as e:  # noqa: BLE001 - keep the run going
        log(f"sbir.gov: unavailable ({e})")
        return None
    items = data if isinstance(data, list) else (data.get("results") or data.get("solicitations") or [])
    out = []
    for s in items:
        title = (s.get("solicitation_title") or s.get("title") or "").strip()
        if not title:
            continue
        num = s.get("solicitation_number") or slug(title)
        out.append(record(
            id=f"sbir-{slug(num)}", source="sbir.gov", source_id=str(num), type="grant",
            name=title, funder=f"{s.get('agency', '')} {s.get('branch') or ''}".strip() or "SBIR/STTR agency",
            level="federal", region="US", eligible_entities=["for-profit"],
            focus=["research", "tech"], must_have_any=["research"],
            deadline=mdy_to_iso(s.get("close_date") or s.get("application_due_date")),
            deadline_text="See solicitation",
            url=s.get("solicitation_agency_url") or s.get("sbir_solicitation_link") or "https://www.sbir.gov/topics",
            requirements=["For-profit US small business, 500 or fewer employees",
                          "Research and development project", "SAM.gov registration (UEI)"],
            documents_typically_needed=["DUNS/UEI + SAM registration", "budget"],
            notes="SBIR/STTR solicitation. Funds R&D, not general operations.",
        ))
    log(f"sbir.gov: {len(out)} open solicitations")
    return out
