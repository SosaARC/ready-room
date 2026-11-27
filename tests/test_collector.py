"""Collector and funnel tests. Network calls are replaced with recorded-shape responses
built from each API's published documentation, so these run offline and in CI.

    python3 -m unittest tests/test_collector.py -v
"""
import datetime as dt
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

import collector.run as runmod
from collector import funnel, grants_gov, sam_gov, sbir

ROOT = pathlib.Path(__file__).resolve().parent.parent
FUT = (dt.date.today() + dt.timedelta(days=60)).strftime("%m/%d/%Y")
SOON = (dt.date.today() + dt.timedelta(days=5)).strftime("%m/%d/%Y")


def gg_fake(url, data=None, **_):
    """Grants.gov search2: opportunity 1 is open to small businesses, 2 to nonprofits, 3 unrestricted."""
    elig = data["eligibilities"]
    hits = []
    if "23" in elig:
        hits.append({"id": "1001", "number": "DOT-TEST-1", "title": "Small Fleet Safety Grant", "agencyCode": "DOT", "agencyName": "Department of Transportation", "openDate": "10/01/2026", "closeDate": FUT, "oppStatus": "posted", "docType": "synopsis", "alnist": ["20.000"]})
    if "12" in elig:
        hits.append({"id": "1002", "number": "HHS-TEST-2", "title": "Community Health Workers", "agencyCode": "HHS", "agencyName": "Health and Human Services", "openDate": "10/01/2026", "closeDate": SOON, "oppStatus": "posted", "docType": "synopsis", "alnist": ["93.000"]})
    if "99" in elig:
        hits.append({"id": "1003", "number": "USDA-TEST-3", "title": "Forecasted Rural Program", "agencyCode": "USDA", "agencyName": "Department of Agriculture", "openDate": "", "closeDate": "", "oppStatus": "forecasted", "docType": "forecast", "alnist": []})
    return {"errorcode": 0, "msg": "Webservice Succeeds", "data": {"hitCount": len(hits), "startRecord": 0, "oppHits": hits}}


class GrantsGov(unittest.TestCase):
    def test_eligibility_comes_from_which_searches_matched(self):
        recs = {r["source_id"]: r for r in grants_gov.collect(fetch=gg_fake, log=lambda *_: None)}
        self.assertEqual(recs["1001"]["eligible_entities"], ["for-profit"])
        self.assertEqual(recs["1002"]["eligible_entities"], ["nonprofit"])
        self.assertIn("for-profit", recs["1003"]["eligible_entities"])
        self.assertEqual(recs["1001"]["funder"], "Department of Transportation")
        self.assertTrue(recs["1001"]["url"].startswith("https://www.grants.gov/"))
        self.assertIsNone(recs["1003"]["deadline"])
        self.assertIn("Forecasted", recs["1003"]["deadline_text"])

    def test_error_payload_raises(self):
        with self.assertRaises(RuntimeError):
            grants_gov.collect(fetch=lambda *a, **k: {"errorcode": 1, "msg": "bad"}, log=lambda *_: None)


class Sam(unittest.TestCase):
    def test_skips_without_key(self):
        with mock.patch.dict(os.environ, {"SAM_API_KEY": ""}):
            self.assertEqual(sam_gov.contracts(log=lambda *_: None), [])
            self.assertEqual(sam_gov.assistance_listings(log=lambda *_: None), [])

    def test_contracts_filter_by_naics_and_state_and_hide_key(self):
        seen = {}

        def fake(url, **_):
            seen["url"] = url
            return {"opportunitiesData": [
                {"noticeId": "abc", "title": "Box truck delivery services", "naicsCode": "484110", "responseDeadLine": FUT, "typeOfSetAside": "SBA", "placeOfPerformance": {"state": {"code": "NC"}, "city": {"name": "Greensboro"}}, "fullParentPathName": "VA"},
                {"noticeId": "def", "title": "IT services", "naicsCode": "541512", "responseDeadLine": FUT, "placeOfPerformance": {"state": {"code": "NC"}}},
                {"noticeId": "ghi", "title": "Courier, Alaska", "naicsCode": "492110", "responseDeadLine": FUT, "placeOfPerformance": {"state": {"code": "AK"}}},
                {"noticeId": "jkl", "title": "Moving, women-owned set-aside", "naicsCode": "484210", "responseDeadLine": FUT, "typeOfSetAside": "WOSB", "placeOfPerformance": {"state": {"code": "VA"}}}]}
        logs = []
        with mock.patch.dict(os.environ, {"SAM_API_KEY": "SECRET123"}):
            out = sam_gov.contracts(fetch=fake, log=logs.append)
        self.assertEqual(sorted(r["source_id"] for r in out), ["abc", "jkl"])
        self.assertTrue(all("SECRET123" not in l for l in logs))
        wosb = next(r for r in out if r["source_id"] == "jkl")
        self.assertEqual(wosb["must_have_any"], ["women-owned"])
        self.assertEqual(wosb["type"], "contract")
        self.assertIn("Small business set-aside", next(r for r in out if r["source_id"] == "abc")["requirements"])


class Sbir(unittest.TestCase):
    def test_down_returns_none(self):
        def boom(*a, **k):
            raise OSError("403 Forbidden")
        self.assertIsNone(sbir.collect(fetch=boom, log=lambda *_: None))

    def test_records_require_research(self):
        out = sbir.collect(fetch=lambda *a, **k: [{"solicitation_title": "NSF SBIR Phase I", "solicitation_number": "NSF 26-1", "agency": "NSF", "close_date": "2027-03-01"}], log=lambda *_: None)
        self.assertEqual(out[0]["must_have_any"], ["research"])
        self.assertEqual(out[0]["deadline"], "2027-03-01")


class RunAndMerge(unittest.TestCase):
    def test_merge_keeps_first_seen_and_keeps_last_good_data_when_a_source_is_down(self):
        with tempfile.TemporaryDirectory() as d:
            live = pathlib.Path(d)
            with mock.patch.object(runmod, "LIVE", live):
                a = lambda log: grants_gov.collect(fetch=gg_fake, log=log)  # noqa: E731
                b = lambda log: [{**sbir.collect(fetch=lambda *x, **y: [{"solicitation_title": "DOE SBIR", "solicitation_number": "DOE-1", "agency": "DOE"}], log=log)[0]}]  # noqa: E731
                runmod.run({"grants.gov": a, "sbir.gov": b}, do_pages=False, log=lambda *_: None)
                first = json.loads((live / "opportunities.json").read_text())
                for r in first:
                    r["first_seen"] = "2026-01-01"
                (live / "opportunities.json").write_text(json.dumps(first))
                runmod.run({"grants.gov": a, "sbir.gov": lambda log: None}, do_pages=False, log=lambda *_: None)
                second = {r["id"]: r for r in json.loads((live / "opportunities.json").read_text())}
                status = json.loads((live / "status.json").read_text())
                report = (live / "REPORT.md").read_text()
        self.assertEqual(second["gg-1001"]["first_seen"], "2026-01-01")
        self.assertIn("sbir-doe-1", second)
        self.assertFalse(status["sources"]["sbir.gov"]["ok"])
        self.assertEqual(status["new"], 0)
        self.assertIn("Closing in the next 3 weeks", report)


class Funnel(unittest.TestCase):
    def setUp(self):
        self.biz = json.loads((ROOT / "tests" / "fixtures" / "starter.json").read_text())
        self.gg = {r["source_id"]: r for r in grants_gov.collect(fetch=gg_fake, log=lambda *_: None)}

    def test_federal_grant_without_sam_registration_is_prepare(self):
        f = funnel.funnel(self.gg["1001"], self.biz)
        self.assertEqual(f["bucket"], "Prepare")
        self.assertTrue(any("SAM.gov" in w for w in f["why"]))

    def test_nonprofit_only_is_skipped_for_an_llc(self):
        self.assertEqual(funnel.funnel(self.gg["1002"], self.biz)["bucket"], "Skip")

    def test_with_sam_registration_and_time_it_is_apply_now(self):
        b = json.loads(json.dumps(self.biz))
        b["profile"]["uei"] = "ABC123DEF456"
        b["answers"].update({k: "x" * 60 for k in ("need", "use_of_funds", "impact", "mission")})
        self.assertEqual(funnel.funnel(self.gg["1001"], b)["bucket"], "Apply now")

    def test_not_enough_time_for_a_one_time_deadline_is_skip(self):
        g = dict(self.gg["1001"], deadline=(dt.date.today() + dt.timedelta(days=3)).isoformat(), deadline_text="")
        f = funnel.funnel(g, self.biz)
        self.assertEqual(f["bucket"], "Skip")
        self.assertIn("Not enough time", f["why"][0])

    def test_curated_catalog_runs_end_to_end(self):
        opps = funnel.load_all()
        res, skip = funnel.run(self.biz, opps)
        self.assertEqual(sum(len(v) for v in res.values()), len(opps))
        self.assertGreater(skip.get("Nonprofits or governments only", 0), 10)


if __name__ == "__main__":
    unittest.main()
