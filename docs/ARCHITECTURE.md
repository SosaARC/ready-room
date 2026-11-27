# Architecture

```
                 ┌──────────────────────────┐
                 │     Business profile     │  entered once
                 └────────────┬─────────────┘
                              │
 Gmail scan ─┐   ┌────────────▼─────────────┐
 AI file read├──▶│      Document vault      │  records + links + expiry
 By hand ────┘   └──────┬─────────────┬─────┘
                        │             │
          ┌─────────────▼───┐   ┌─────▼──────────────────────┐
          │  Broker packets │   │        Grant finder         │
          │ checklist, email│   │ 1. rules screen (code)      │
          │ status tracking │   │ 2. score: focus, docs, date │
          └─────────────────┘   │ 3. Claude ranks top matches │
                                └─────┬──────────────────────┘
                                      │ save
                 ┌────────────────────▼─────────┐
                 │  Applications + answer bank  │
                 │ Claude drafts from the bank  │
                 └──────────────────────────────┘
```

## Data

One JSON object per business:

```json
{
  "id": "...",
  "profile": { "name": "", "entityType": "llc", "county": "", "state": "NC", "focus": [] },
  "documents": [{ "type": "coi", "issuer": "", "issued": "", "expires": "", "link": "" }],
  "brokers":   [{ "name": "", "kind": "broker", "method": "RMIS", "required": ["mc_authority", "coi"],
                 "coi": "Requested from agent", "agreement": false, "minDays": "90", "status": "Pending approval" }],
  "answers":   { "mission": "", "need": "" },
  "pipeline":  [{ "grantId": "", "status": "Drafting", "deadline": "", "docsDue": "", "reportDue": "",
                 "checklist": [], "budget": [], "answers": [{ "q": "", "a": "" }], "versions": [] }],
  "customGrants": []
}
```

Storage picks the best option the page has:

1. **Claude artifact database:** `data/users/<viewer id>/biz_<id>`. This path is private to the viewer, even from anyone the page is shared with.
2. **Browser localStorage:** when opened as a plain file.
3. **Memory:** if the browser blocks storage. The Data screen tells the user to copy a backup.

## Grant matching

`assess(grant, business)` runs before any AI call. A program is screened out when:

- **Entity:** the business's class (for-profit, nonprofit, government) is not in `eligible_entities`. Sole proprietors also match "individual". Nonprofits that are pending or fiscally sponsored get a note when a 501(c)(3) letter is expected.
- **Place:** a local program's `region` doesn't name the business's county or city, or a state program is outside the business's state. `area_check` programs pass with a note to check the address against the program map.
- **Restricted groups:** `must_have_any` (women-owned, veteran or military spouse, agriculture, R&D, export, disability services) isn't in the profile.
- **Excluded types:** `excludes_any` matches the profile. A trucking industry automatically counts as a local service business.
- **Age and size:** below `min_years`, or outside `employees_range`.
- **Closed:** the deadline has passed and the program does not recur.

Loans are flagged and hidden by default. Non-grant `kind`s (contract, matched savings, training reimbursement) are labeled on the card. What remains is scored on focus overlap, deadlines within 45 days, and the share of the program's usual documents already in the vault. Claude ranks the top 18.

## AI calls

All AI calls ask for JSON and include only the profile, the answer bank and the specific program. Every prompt tells Claude to use only the facts given and to mark missing facts as `[NEED: ...]`.

| Feature | Input | Output |
| --- | --- | --- |
| Read a document | PDF text (pdf.js, first 4 pages) or a photo | type, issuer, dates, notes, shown in a form for review |
| Sort Gmail results | subject, sender and snippet of each email | document type, or skip for sales emails |
| Rank grants | profile plus up to 18 screened programs | fit, reason, gap |
| Fill a custom grant | pasted announcement text | name, funder, amount, deadline, eligibility |
| Draft answers | profile plus answer bank | answer bank sections |
| Draft an application | profile, answer bank, program, budget, pasted questions | one answer per question, within stated limits |
| Short versions | one answer bank section | 50- and 150-word versions |
| Client intake | a client's pasted reply | profile fields (empty fields only) |
