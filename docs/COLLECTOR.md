# The collector and the funnel

Ready Room finds every grant it can, then narrows the list to the few a business can actually win.

## 1. Collect (every night, on GitHub)

`.github/workflows/collect.yml` runs `python -m collector.run` at 4:17 am Eastern. It can also be started by hand from the Actions tab ("Run workflow").

| Source | What it adds | Access | Notes |
| --- | --- | --- | --- |
| Grants.gov `search2` | Every posted and forecasted federal grant | Public, no key | One search per applicant group (small business, for-profit, nonprofit, individual, government, tribal, unrestricted). Grants.gov's search results don't include eligibility, so each grant is tagged by which searches it appeared in. |
| SAM.gov Get Opportunities | Federal **contracts** in NC and nearby states, for the trucking, courier, moving, warehousing and waste NAICS codes in `collector/sam_gov.py` | Free key (`SAM_API_KEY` secret) | Not grants: paid work, often set aside for small, women-owned or veteran-owned businesses. One request per night. |
| SAM.gov Assistance Listings | Active federal grant **programs** (the old CFDA catalog) | Same key | Reference only. Open calls under these programs arrive through Grants.gov. A personal key with no SAM.gov role gets about 10 requests a day, so this is one request per night. |
| SBIR.gov | Open SBIR/STTR research solicitations | Public, no key | SBIR.gov has marked its API as under maintenance at times. When it's down, the run keeps the last good data. |
| Curated catalog (`data/grants.json`) | Local, North Carolina and private programs with no API | Checked by a person | The page watcher fingerprints each official page every night and lists the ones that changed in `data/live/REPORT.md`, so a person re-checks deadlines and amounts. It respects robots.txt and never copies page content into the catalog on its own. |

**Not collected on purpose:** LinkedIn (its user agreement prohibits scraping), and sites that block automated visits. Paste those announcements into "Add a grant I found", and Claude fills in the fields.

**Output:** `data/live/opportunities.json` (every source in one schema), `status.json` (per-source health), `REPORT.md` (new, closing soon, pages that changed). The build step bakes these into the app, and the run publishes it to GitHub Pages.

## 2. Funnel (in the app and in `collector/funnel.py`)

| Stage | Question | How |
| --- | --- | --- |
| Can you apply? | Hard rules | Entity type, place, restricted groups, excluded business types, minimum age and size, loans, closed one-time deadlines |
| Should you? | Fit | Focus areas, industry, local and state bonus, share of the usual documents already on file |
| Can you win it in time? | Timeline, credentials, competition | Prep time: about 10 days local, 14 state, 21 federal, 10 for a contract, plus 28 for a first SAM.gov registration, 3 per missing document and 5 if the core answers aren't written. Competition: local and state pools beat national lotteries, and programs with 3 or fewer awards are long shots. |

Every opportunity lands in **Apply now**, **Prepare for**, or **Skip**, with the reasons. A recurring program whose deadline is too close moves to Prepare (for the next round). A one-time deadline that's too close is skipped.

From the command line, with any Ready Room backup or starter file:

```bash
python -m collector.funnel my-business.json --md funnel.md
```

The nightly run writes a funnel report for every file in `profiles/` to `data/live/funnels/`. **The repo is public, so only put example or anonymized businesses there.** Keep real client files out of the repo; run the funnel on them locally or in the app.

## 3. Set up (one time)

1. **SAM.gov key:** sign in at sam.gov, open Account Details, and generate a Public API Key. In this repo, open Settings, then Secrets and variables, then Actions, choose New repository secret, and add it as `SAM_API_KEY`. Never paste the key in an issue, commit or chat.
2. **Pages:** in Settings, then Pages, set Source to "GitHub Actions". The site publishes the portfolio at the root and the app at `/app/`.
3. **First run:** Actions, then Collect opportunities, then Run workflow.

## Tests

`python3 -m unittest tests/test_collector.py` runs 12 offline tests for the collector and the funnel, using recorded-shape responses from each API's documentation. `npm test` runs those plus the app tests.
