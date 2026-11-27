# Ready Room

[![Tests](https://github.com/SosaARC/ready-room/actions/workflows/test.yml/badge.svg)](https://github.com/SosaARC/ready-room/actions/workflows/test.yml) [![Collect opportunities](https://github.com/SosaARC/ready-room/actions/workflows/collect.yml/badge.svg)](https://github.com/SosaARC/ready-room/actions/workflows/collect.yml)

**One business profile and one document vault, reused for broker setup packets and grant applications.**

Built by Jordan Hairston for 5908 Logistics, a box truck carrier in Winston-Salem, NC, and for the small business owners he helps find and apply for grants.

## The problem

Small business owners hand over the same paperwork again and again.

- **Carriers:** every freight broker and load board asks for the same setup packet: operating authority, certificate of insurance, W-9, payment details and a signed agreement. Documents expire, brokers reject incomplete packets, and nobody tracks which broker has what.
- **Grant seekers:** every application asks for the same documents and the same ten questions in different words. Owners lose hours on programs they were never eligible for, because many "small business grants" only fund nonprofits or are really loans.

## What Ready Room does

| Part | What it does |
| --- | --- |
| **Today** | What needs attention now, with carrier readiness and grant readiness shown separately. New businesses get a five-step setup checklist that names what is missing. |
| **All businesses** | Every business you manage in one table, plus every deadline and expiry date in the next 90 days. Exports to your calendar (.ics) with 7-day reminders. |
| **Business profile** | Entered once: entity type, location, carrier details (USDOT, MC, authority date, equipment, ELD, insurance agent) and grant focus areas. Includes a client intake questionnaire, and Claude can fill the profile from a client's reply. |
| **Document vault** | Every document with its expiry date and a link to where the file lives. Three ways in: by hand, a PDF or photo read by Claude, or a Gmail scan for attachments and onboarding invites. |
| **Broker setups** | One record per broker or platform: how it onboards (Highway, RMIS, MyCarrierPackets, a portal), a COI naming that broker, the agreement, minimum authority age, status and carrier ID. A carrier info panel copies one field at a time for portals. Drafts COI requests to your insurance agent for one broker or several, and "Check Gmail for approvals" suggests status and carrier ID updates from onboarding emails. |
| **Shortlist** | The funnel: every opportunity sorted into Apply now, Prepare for, or Skip, using eligibility, fit, prep time (documents, SAM.gov registration, written answers) and the size of the applicant pool. Each one says why. |
| **Grant finder** | A catalog of 64 local, North Carolina, federal and national programs, each checked on its official page. Rules screen out programs a business cannot apply for (entity type, place, restricted groups, excluded business types, age, size, loans), then Claude ranks what is left. |
| **Answer bank** | 20 sections that most applications ask for, drafted from the profile, with 50- and 150-word short versions. Any section can be reused from another business you manage. |
| **Grant applications** | Prospect through Reporting. Client and report dates, an attachments checklist, a budget with match, and one answer per question with live counts against word limits. Keeps the last 5 drafts. |

## Collector

A nightly GitHub Action pulls every posted federal grant from Grants.gov, federal contracts and program listings from SAM.gov, and SBIR/STTR solicitations, then watches the official pages behind the curated catalog for changes. See `docs/COLLECTOR.md` for the sources, the funnel's rules and one-time setup.

## Design choices

- **No files stored.** The vault keeps records and links. Files stay in Gmail, Drive or on the owner's device. This keeps EINs and bank details out of another database.
- **Screen before you rank.** Eligibility rules (entity type, location, loan or grant) run first in plain code, so the AI only spends time on programs the business can actually apply for.
- **AI drafts, people decide.** Claude never submits anything. Every draft is editable, and missing facts are marked so nothing gets made up.
- **Multi-business.** One person can manage several businesses. That's how a grant writer or a nonprofit supporting local owners would use it.

## Run it

Ready Room is one HTML file with no build step beyond inserting the catalog.

```bash
python3 build.py          # writes dist/index.html
open dist/index.html      # works in any browser; data saves in that browser
```

Opened inside Claude as an artifact, it also saves privately to the owner's Claude account, uses Claude to read documents and draft answers, and can scan Gmail through the Gmail connector. A starter or backup file loads from the welcome screen or Your data. Opened as a plain file, the profile, vault, broker tracking, grant screening and applications all still work. The AI buttons explain that they need Claude.

### Tests

```bash
npm install
npm test               # 73 app checks plus 12 collector and funnel tests
npm run test:browser   # focus, scrolling and phone-width checks in Chrome (set CHROME_PATH)
```

### Refresh federal opportunities

```bash
python3 scripts/fetch_grants_gov.py --keyword "small business" --eligibility 23 22
```

This uses the public Grants.gov `search2` API (no key). Review `data/grants-gov.json`, then copy the programs that fit into `data/grants.json`.

## Repository

```
src/app.html                  the app (HTML, CSS, JavaScript in one file)
dist/index.html               the built app, ready to open or host
data/grants.json              verified program catalog
data/not-grants.json          things marketed as grants that are not
data/SOURCES.md               where each program was checked
collector/                    nightly collector (Grants.gov, SAM.gov, SBIR.gov, page watcher) and funnel
scripts/fetch_grants_gov.py   one-off Grants.gov pull (older)
.github/workflows/            nightly collection, tests on every change, GitHub Pages
build.py                      inserts the catalog and writes dist/index.html
docs/ARCHITECTURE.md          how the pieces fit
docs/portfolio.html           portfolio case study page
gpt/                          the grant screener as a ChatGPT custom GPT
CHANGELOG.md                  build log: what each review found and what changed
tests/                        integration, unit and browser tests
```

## Status and next steps

Built in rounds. See `CHANGELOG.md` for what each review found and what changed.

- [x] Profile, vault, broker setups, grant finder, answer bank, grant applications
- [x] AI document reading, Gmail scan, AI ranking, drafting and client intake
- [x] All-businesses view and calendar export
- [x] Starter file, setup checklist, Gmail approval suggestions
- [ ] First real users: 5908 Logistics broker setups and grant clients, starting December 2026
- [ ] Shareable, expiring packet links for brokers

## License

MIT. See `LICENSE`.
