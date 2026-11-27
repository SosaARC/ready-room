"""Shared helpers for the opportunity collector: HTTP with retries, dates, the record schema."""
import datetime as dt
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "ReadyRoom-Collector/1.0 (+https://github.com/; grant matching for small businesses)"
TODAY = dt.date.today().isoformat()

# Every source is normalized to the same record shape the app already reads (data/grants.json),
# plus a few collector fields: source, source_id, type, first_seen, last_seen, award_ceiling, expected_awards.
SCHEMA_DEFAULTS = {
    "id": "", "name": "", "funder": "", "level": "federal", "region": "US",
    "eligible_entities": [], "focus": ["general"], "amount_min": None, "amount_max": None,
    "amount_text": "See notice", "deadline": None, "deadline_text": "", "requirements": [],
    "documents_typically_needed": [], "is_loan": False, "url": "", "verified_on": TODAY,
    "notes": "", "must_have_any": [], "excludes_any": [], "kind": "grant", "area_check": False,
    "min_years": None, "employees_range": None,
    "source": "", "source_id": "", "type": "grant", "first_seen": TODAY, "last_seen": TODAY,
    "award_ceiling": None, "expected_awards": None,
}


def record(**kw):
    r = dict(SCHEMA_DEFAULTS)
    r.update({k: v for k, v in kw.items() if v is not None or k in ("deadline", "amount_max", "amount_min")})
    return r


def slug(s, n=60):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")[:n]


def mdy_to_iso(s):
    """Grants.gov and SAM.gov use MM/DD/YYYY; return YYYY-MM-DD or None."""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return dt.datetime.strptime(s[:25], fmt).date().isoformat()
        except ValueError:
            continue
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    return m.group(1) if m else None


def http(url, data=None, headers=None, tries=3, timeout=40):
    """GET (or POST JSON when data is given). Returns parsed JSON. Retries on 429/5xx with backoff."""
    body = None
    h = {"User-Agent": UA, "Accept": "application/json"}
    if data is not None:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    last = None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=body, headers=h, method="POST" if body else "GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt * 3)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(2 ** attempt * 3)
    raise last


def redact(url):
    """Never print API keys in logs."""
    return re.sub(r"(api_key=)[^&]+", r"\1***", url)
