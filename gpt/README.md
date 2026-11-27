# Ready Room as a custom GPT

Most small business owners already use ChatGPT. This folder packages Ready Room's grant screening and drafting rules as a custom GPT, so an owner can get the core of it without a new app. It's also the version to bring to an OpenWorks community day.

## Set it up (about 10 minutes)

1. In ChatGPT, open **Explore GPTs**, then **Create**, then **Configure**.
2. **Name:** Ready Room Grant Helper
3. **Description:** Screens North Carolina small business grants you can actually apply for, then drafts answers from facts you give it.
4. **Instructions:** paste everything in `INSTRUCTIONS.md`.
5. **Knowledge:** upload `../data/grants.json` and `../data/not-grants.json`.
6. **Conversation starters:**
   - Which grants can my business actually apply for?
   - Is this "grant" really a grant? (paste the offer)
   - Help me write my need statement
   - What documents should I gather before I apply?
7. **Capabilities:** turn on Web Search so it can check deadlines on official pages. Turn off image generation.
8. Save it as "Only me" or "Anyone with the link," then test it with the checklist below.

## Test checklist

Run each one and note what happened. These results are your before/after evidence.

- [ ] A for-profit trucking LLC in Forsyth County asks for grants. It should not list nonprofit-only programs or women-owned-only programs.
- [ ] Paste a "government grant, just pay a processing fee" message. It should flag it as a likely scam and cite the not-grants list.
- [ ] Ask for a need statement with no facts given. It should ask questions or write [NEED: ...] instead of inventing numbers.
- [ ] Ask about a program's deadline. It should give the date and tell you to confirm on the official page.
