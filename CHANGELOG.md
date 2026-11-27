# Build log

Ready Room is built in rounds. Each round ends with reviews by reviewers who did not build it. So far these are AI reviewers, each given one role: a fact-checker, a new owner-operator, a grant writer managing 15 clients, and an OpenWorks program reviewer. They read the code and data and report problems. The next round acts on what they found. Feedback from real users starts in December 2026 and will be logged here the same way.

## Design decisions

- **Rules first, AI second.** Eligibility runs in plain code before any AI call. A model reading program text has to guess at rules it can't verify; code gives the same answer every time and can be checked. Claude only ranks and explains what passes.
- **Records, not files.** The vault stores what a document is, when it expires and where it lives. Carrier and grant documents hold EINs and bank details, so the files stay in Gmail, Drive or on the owner's device.
- **Missing facts stay visible.** Every AI draft marks gaps as [NEED: ...] instead of filling them in.

## Round 1: first working version (Nov 26, 2026)

**Built**
- Business profile, document vault with expiry tracking, broker packet checklists and setup email, grant finder, answer bank, applications pipeline
- Document reading with AI (PDF text or photo), Gmail scan for document attachments, Claude ranking and drafting
- Grant catalog: 41 programs checked on official pages, plus 12 things sold as "grants" that are not

**What review found, and what changed**
- *The sample business (not women-owned, not a veteran, not a farm) was shown the Amber Grant, Hiring Our Heroes and AgVentures.* Added a `must_have_any` rule to the catalog and screen, so programs restricted to one group only show for businesses in that group.
- *Programs with monthly or annual rounds showed "Deadline passed" the day after a round closed.* Recurring programs now say to check the next round.
- *NC IDEA SEED excludes local service businesses, but the card didn't say so.* Every card now shows the program's key rules.
- *North Carolina ended HUB certification on July 7, 2026.* Replaced with NCSBE in the document types.
- *The application essay claimed results the tool doesn't have yet.* Rewritten to describe only what has really happened, plus what is being measured.

## Round 2: carrier, grant writer and program reviewer roles (Nov 26, 2026)

Three role-played AI reviewers read the code and data from their role's point of view. After that, real screenshots were taken on desktop and phone.

**What the owner-operator review found, and what changed**
- *"Brokers onboard through portals, not email, and Highway is a platform, not a broker."* Each setup now records how the broker onboards (Highway, RMIS, MyCarrierPackets, Carrier Assure, a portal or an app). "Copy setup email" became "Copy carrier info" for pasting into portals.
- *"Each broker needs its own COI naming it as certificate holder, and the agreement is signed during onboarding."* Each broker now has its own COI status, an "Email agent for COI" draft, and an agreement checkbox.
- *"Brokers want your authority to be a minimum age."* Added the authority grant date, days active, and a per-broker minimum with a warning.
- *"The readiness number averaged carrier and grant work, so a full packet looked like 33%."* Today now shows carrier readiness and grant readiness separately.
- Added carrier details brokers ask for every time (equipment, lanes, ELD, factoring, after-hours contact, insurance agent), BOC-3, UCR and MCS-150 document types, separate checklists for gig apps, and onboarding invites in the Gmail scan.

**What the grant writer review found, and what changed**
- *"With 15 clients I can't switch through each one to see what's due."* Added **All businesses**: one table across every client plus every date in the next 90 days, with a calendar export (.ics) and 7-day reminders.
- *"The screen lets a one-truck LLC through to NC IDEA SEED, SBIR, export grants and an IDA it's too new for."* Encoded those rules: excluded business types, R&D-only and export-only programs, minimum business age, and employee range. The sample carrier went from 14 "eligible" programs to 6 real ones.
- *"Stages stop at Awarded."* Stages now run Prospect, LOI sent, Invited, Drafting, Submitted, Under review, Awarded, Reporting, Declined and Closed, with client document dates, a draft due date, a report due date, a contact and the amount awarded.
- *"Drafting is one text box."* Each question is now its own answer with a live word or character count against the limit stated in the question. The last 5 drafts are kept, and drafts download as a document.
- Added a budget builder (grant, cash match, in-kind) that warns when the ask goes over the program maximum, an attachments checklist for each application, nine more answer bank sections for nonprofits, and 50- and 150-word short versions.
- Added nonprofit entity types (501(c)(3) pending, fiscally sponsored, other), a client intake questionnaire, and "fill profile from their answers."

**What the program review found**
- *"Show it working, not mockups; show how it was built; one real workshop outline."* The portfolio now uses real screenshots, this build log and a workshop agenda. A ChatGPT version (custom GPT instructions) lives in `gpt/`.

**Found in screenshots:** the grant finder was wider than a phone screen. Fixed the grid sizing and long chips.

## Round 3: QA engineer, second-pass role review, catalog research (Nov 26, 2026)

A QA review ran the app in a scripted browser and tried to break it. The owner-operator and grant writer roles came back to check whether the round 2 fixes worked. A research pass added more Triad programs.

**Bugs the QA review found and verified, now fixed**
- *Typing a date or amount lost focus mid-entry, so a deadline could save as year 0002.* The page now waits until you leave the field before redrawing.
- *An AI draft started for one business could save into another if you switched while it ran.* Each AI result is now tied to the business it started on.
- *On phones the page jumped to the top after every tap.* Fixed the tab row scrolling.
- *A deleted business could come back if a save was in flight.* Deletes now wait for pending saves.
- *The last second of typing could be lost when closing the tab.* Pending saves now flush when the page is hidden.
- *"2,000-character limit" was read as a limit of 0.* Limits with thousands separators now parse correctly.
- *A renewed document kept showing the old one as expired.* Only the newest copy of each document type counts.
- *"Today" used the UTC date, so after 7 pm ET it was already tomorrow.* Dates are now local.
- *A city named Davidson matched programs for Davidson County.* County and city matching now uses whole words.
- *Calendar events used list positions as IDs, so re-importing changed the wrong events.* IDs are now stable, and long lines are folded to the calendar standard.
- Dialogs return focus where you were. Unknown statuses from old backups are mapped instead of disappearing. No security holes found: untrusted text from AI, Gmail, the catalog and user input is always escaped.

**What the second-pass role reviews found, and what changed**
- *Today counted a COI with 40 days left as missing, while broker cards called it usable.* Both now agree, and Today notes what is expiring.
- *Portals take one field at a time.* Added a carrier info panel with a copy button for each field, including insurer, limits and COI dates.
- *When the policy renews, every broker's COI has to be reissued.* Ready Room now flags it. A new "COI request for all brokers" button writes one email to the agent listing every certificate holder.
- *The certificate holder field was hidden, so the COI email said "I'll send it later."* It now shows on the card until the COI comes back. An approved broker with no signed agreement gets flagged.
- *Blank founded year or headcount counted as a pass.* Those programs now say what to fill in. Encoded more rules: 501(c)(3)-only programs exclude other nonprofits, the diesel replacement grant needs an older diesel to replace, PTRC training needs 12 months in business, and arts grants need an arts focus.
- *The over-maximum warning used past award sizes.* It only fires when the program states a cap ("up to", "maximum").
- *Claude's grant ranking disappeared when switching clients.* It is now saved per business with its date. A "Check all businesses" button on each grant shows which clients pass and why.
- *Intake answers about who they serve and results were dropped.* They now fill the community and track record sections. Drafts download as a Word document, the first budget line fills from the ask, and dates in All businesses link to the business.
- Fixed facts: Hiring Our Heroes' December deadline is ET, not EDT, and the DUNS label is now "SAM.gov registration (UEI)".

**Catalog:** 23 more programs verified on official pages, mostly Triad facade grants, community foundations and state programs. 64 programs total. Dropped programs that were retired, loans, or couldn't be confirmed for 2026.

**Tests:** 33 integration checks and 11 unit checks run against every build, plus real-browser checks for focus, scrolling and phone width.

## Round 4: making it the owner's own (Nov 26, 2026)

The first three rounds used a fictional sample. This round prepares Ready Room for its first real user, 5908 Logistics.

- **Starter file.** A business can start from a file (Your data, then "Restore from a backup or starter file"). The 5908 Logistics starter includes the real carrier details and the ten brokers and platforms already in progress, so nothing is retyped.
- **Get set up.** Until a business is set up, Today shows a five-step checklist (profile basics, carrier or grant details, documents with expiry dates, first setups or grants, two written answers), and each step links to where you finish it.
- **Check Gmail for approvals.** Searches the last 60 days for onboarding emails from RMIS, Highway, MyCarrierPackets and brokers. Claude reads them and suggests updates ("TQL: approved, carrier ID ..."). Nothing changes until you accept, and unknown brokers can be added as new setups.
- **Reuse across businesses.** Any answer bank section can be copied from another business you manage, such as a grant writer's own bio or boilerplate, then edited.
- Tests: 8 more checks for the starter file, the setup checklist, approval suggestions and reuse.

## Round 5: first-time user test on a phone (Nov 26, 2026)

A role-played first-time user (the owner of 5908 Logistics, on a phone) loaded the starter file and tried four real tasks in a scripted Chrome browser, taking 38 screenshots along the way.

**What blocked him, and what changed**
- *On first open there was nowhere to load the starter file.* The welcome screen now has a file picker. Restoring into an empty new business replaces it instead of making a duplicate. (Testing this fix in a real browser caught one more bug: the welcome-screen picker did nothing until a business existed. Fixed.)
- *Carrier info for portals hid its labels on a phone and jumped to the first Copy button.* Each field now shows its label above the value, the dialog opens at the top, and it lists fields that are still blank.
- *"COI request for all brokers" marked every broker requested before anything was sent, left holder addresses blank without warning, and signed the email as the LLC.* It now opens a list to pick brokers, shows a preview that flags missing holder addresses, signs with your name, and only marks them requested after you say you sent it. The holder field is now a multi-line box.
- *"At least 3 documents, with expiry dates" stayed To do with no reason.* The step now names what is missing ("Add expiry dates: Certificate of insurance").
- *Ten near-identical "1 document missing" rows on Today, and ten fully expanded broker cards.* Missing documents are now grouped ("Notice of assignment missing: holds up 6 setups"), the setup checklist comes first, and each broker card's update fields fold away.
- *A nonprofit client got business defaults.* New businesses ask for the type up front. Added focus areas for youth and education, health, low-income residents and economic mobility. The grant finder's wording matches the client type, and client intake moves to the top of an empty profile.
- *The checklist said "Budget missing" with a budget right below it.* A budget built in the application now satisfies that item.

**Polish found in screenshots:** the phone tab row stretched on short pages, status chips were cut to "S…", budget item boxes were crushed, table labels overlapped values on phones, tab labels wrapped into each other, the toast was too narrow, collapsible sections had no arrow, and raw tags like "community-development" showed. All fixed.

**Starter file:** added the owner's name for signatures, and flagged Convoy (the original company shut down in 2023) to confirm.

**Tests:** 13 more checks. 65 automated checks in all, plus real-browser checks for focus, scrolling and phone width.

## Round 6: find every grant, then funnel down (Nov 26, 2026)

The goal changed from "a curated catalog" to "every grant we can find, narrowed to the ones a business can win."

- **Collector.** A nightly GitHub Action pulls every posted and forecasted federal grant from Grants.gov (tagged by who may apply), federal contracts in NC and nearby states for trucking, courier, moving and warehousing work from SAM.gov, active federal grant programs from SAM.gov's Assistance Listings, and open SBIR/STTR solicitations. A failed source keeps its last good data instead of stopping the run. SAM.gov's free key allows about 10 requests a day, so each source makes one large request.
- **Page watcher.** The 64 curated programs have no APIs. Each night the watcher fingerprints their official pages (respecting robots.txt) and lists the ones that changed, so a person re-checks them.
- **Not scraped on purpose:** LinkedIn, whose user agreement prohibits it, and sites that block automated visits. Those go through "Add a grant I found."
- **Shortlist.** A new screen sorts every opportunity into Apply now, Prepare for, or Skip. It weighs eligibility, fit, prep time (missing documents, a first SAM.gov registration, unwritten answers) and the size of the applicant pool. Every card says why, and Prepare cards list what to do first. The same rules run from the command line (`python -m collector.funnel`) and nightly for each example business in `profiles/`.
- **Scale.** The grant finder now pages 60 at a time. A simulated nightly run of 1,500 federal records renders the Shortlist in about 65 ms in tests.
- **First real result (curated catalog only, before the first nightly run):** 5908 Logistics has 4 to apply for now, 5 to prepare for, and 55 skipped. Most skips were nonprofit-only programs (31). The funnel's clearest finding: without a SAM.gov registration, a one-truck carrier can't meet a typical 30-day federal contract deadline. Registering early is what opens up federal work.
- Tests: 12 offline collector and funnel tests using recorded-shape API responses, and 8 Shortlist checks. 73 app checks in all.
