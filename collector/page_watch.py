"""Watch the official pages behind the curated catalog (data/grants.json).

State and local programs have no APIs. Instead of scraping them into records blindly,
we fingerprint each official page every run and flag the ones that changed, so a person
can re-check deadlines and amounts and update data/grants.json. Respects robots.txt.
"""
import hashlib
import html
import re
import urllib.parse
import urllib.request
import urllib.robotparser

from .common import UA

_robots = {}


def allowed(url):
    p = urllib.parse.urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    rp = _robots.get(base)
    if rp is None:
        rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
        try:
            rp.read()
        except Exception:  # noqa: BLE001 - unreadable robots.txt: be conservative and skip
            rp = False
        _robots[base] = rp
    return bool(rp) and rp.can_fetch(UA, url)


def fingerprint(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(2_000_000).decode("utf-8", "replace")
    text = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text).strip()
    # Ignore copyright years and footers that change every year.
    text = re.sub(r"(©|copyright)\s*\d{4}", "", text, flags=re.I)
    return hashlib.sha256(text.encode()).hexdigest()[:16], text[:20000]


def check(catalog, previous, log=print):
    """Return (new_hashes, changed, failed). previous maps url -> hash."""
    hashes, changed, failed = {}, [], []
    for g in catalog:
        url = g.get("url") or ""
        if not url.startswith("https://") or url in hashes:
            continue
        if not allowed(url):
            failed.append((g["id"], url, "robots.txt does not allow automated checks"))
            hashes[url] = previous.get(url, "")
            continue
        try:
            h, _ = fingerprint(url)
        except Exception as e:  # noqa: BLE001
            failed.append((g["id"], url, str(e)[:80]))
            hashes[url] = previous.get(url, "")
            continue
        hashes[url] = h
        if previous.get(url) and previous[url] != h:
            changed.append((g["id"], g["name"], url))
    log(f"page watch: {len(hashes)} pages, {len(changed)} changed, {len(failed)} could not be checked")
    return hashes, changed, failed
