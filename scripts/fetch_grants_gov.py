#!/usr/bin/env python3
"""Pull open federal opportunities from the public Grants.gov search2 API.

No API key is needed. Run it on your own computer:

    python3 scripts/fetch_grants_gov.py --keyword "small business" --eligibility 23 22
    python3 build.py

It writes data/grants-gov.json in the same shape as data/grants.json.
build.py does not merge it automatically: review the results first, then copy the
ones that fit into data/grants.json.

Eligibility codes used most here (from Grants.gov):
  22 = For-profit organizations other than small businesses
  23 = Small businesses
  12 = Nonprofits with 501(c)(3) status
  25 = Others
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import urllib.request

API = "https://api.grants.gov/v1/api/search2"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def search(keyword, eligibilities, rows):
    body = {
        "rows": rows,
        "keyword": keyword,
        "oppStatuses": "forecasted|posted",
        "eligibilities": "|".join(eligibilities),
    }
    req = urllib.request.Request(
        API,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errorcode") not in (0, None):
        raise SystemExit(f"Grants.gov error: {payload.get('msg')}")
    return (payload.get("data") or {}).get("oppHits") or []


def to_date(s):
    # Grants.gov returns MM/DD/YYYY.
    try:
        return dt.datetime.strptime(s, "%m/%d/%Y").date().isoformat()
    except (TypeError, ValueError):
        return None


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", default="small business")
    ap.add_argument("--eligibility", nargs="*", default=["23", "22"])
    ap.add_argument("--rows", type=int, default=50)
    args = ap.parse_args()

    entities = []
    if {"22", "23"} & set(args.eligibility):
        entities.append("for-profit")
    if "12" in args.eligibility:
        entities.append("nonprofit")

    today = dt.date.today().isoformat()
    out = []
    for hit in search(args.keyword, args.eligibility, args.rows):
        number = hit.get("number", "")
        out.append({
            "id": "gg-" + slug(number or hit.get("title", "")),
            "name": hit.get("title", ""),
            "funder": hit.get("agency") or hit.get("agencyCode", ""),
            "level": "federal",
            "region": "US",
            "eligible_entities": entities,
            "focus": ["general"],
            "amount_min": None,
            "amount_max": None,
            "amount_text": "See notice",
            "deadline": to_date(hit.get("closeDate")),
            "deadline_text": "Forecasted" if hit.get("oppStatus") == "forecasted" else ("See notice" if not hit.get("closeDate") else ""),
            "requirements": [],
            "documents_typically_needed": ["DUNS/UEI + SAM registration", "budget"],
            "is_loan": False,
            "url": f"https://www.grants.gov/search-results-detail/{hit.get('id')}",
            "verified_on": today,
            "notes": f"Grants.gov {number}. Read the full eligibility section before applying.",
        })
    dest = ROOT / "data" / "grants-gov.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {len(out)} opportunities to {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
