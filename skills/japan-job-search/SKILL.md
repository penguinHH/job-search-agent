---
name: japan-job-search
description: Job-search workflow for a candidate looking for a tech-startup job in Japan (the candidate's facts live in the data folder's profile). Uses the local SQLite company database (Global Brains portfolio, J-Startup, METI university ventures + scraped company websites) and profile database in this repository. Use this skill whenever the user asks to find, rank, evaluate or compare companies; research a specific startup or its open positions; write or polish a cold email, cover letter, 志望動機, application-form answers, or a reply to a company; prepare for an interview; update or review job-search progress; update their profile/CV; or add a new VC portfolio or company source - even if they don't say "skill", "database" or "job search" explicitly (e.g. "〇〇这家公司怎么样", "帮我给〇〇写封信", "对方回信了", "我明天面试").
---

# Japan startup job search

You (Claude Code) work alongside the user's GUI agent (`agent_app`, see below): both use the same database,
data folder and rules. You read the databases, judge fit yourself, research live on the web, write drafts, and
record everything back into the database so the next session (yours or the GUI agent's) can pick up where this
one stopped.

Talk with the user in Chinese. Write company-facing drafts in the company's language.

Rules shared with the GUI agent (read the relevant one before scoring or writing):
- `agent_app/kb/outreach.md` – how to write to companies (channels, language, e-mail / cover-letter /
  reply / interview-prep structure).
- `agent_app/kb/scoring.md` – 0–100 fit-scoring rubric.
- `资料/knowledge.md` – personal rules and state: "候选人专属写作规则" (start date, visa, what not to disclose
  about the current employer, self-PR strengths, which mailbox), "评分锚点" (calibration anchors), channel lessons, status.
- `agent_app/reviewer_kb/` – grammar / keigo / document conventions used by the writing reviewer.

## Where things are

Project root: the repository root (run all commands from there). Code is in the root; everything personal
(database, profile, documents, owner.json, knowledge.md) is in the data folder `资料/` (config.HOME).

| Thing | Location |
|---|---|
| DB (SQLite) | `资料/data/jobsearch.db` — tables `companies`, `profile_docs`, `profile_summary`, `matches`, `outreach` |
| DB CLI (no LLM) | `python jobdb.py <cmd>` — run `python jobdb.py -h` or read its docstring for all commands |
| Hand-written profile | `资料/profile/profile.md` (the user's own words; highest priority) |
| CV / papers | `资料/profile/materials/` (docx/pdf/md, extracted into `profile_docs`) |
| Scrapers | `scrapers/globalbrains.py` (portfolio list), `scrapers/enrich.py` (company website, careers page, public emails) |
| Drafts | `资料/outbox/*.md` (created by `jobdb.py save-draft`) |
| Past score batches | `资料/data/scores_*.json` |
| Ranking export | `资料/data/ranking.csv` (`python jobdb.py export`) |

On Windows, prefix Python commands with `PYTHONIOENCODING=utf-8` when using the Bash tool if Japanese
text comes out garbled; `jobdb.py` already reconfigures stdout.

## Shared with the GUI agent (agent_app)
The user also runs a GUI agent (`python -m agent_app`, http://127.0.0.1:8765) on the same database. Keep the
two in sync:
- Read `资料/knowledge.md` at the start of a job-search task and update it (status, channel lessons,
  rules) when something new is learned - the agent loads it into every conversation.
- Extra tables written by the agent: `actions` (approval queue: email / form_submit, status pending/done/
  rejected/failed), `inbox` (fetched job mail matched to companies), `chats`. Check pending actions and new
  inbox rows before acting, so you don't duplicate an application or reply the agent already prepared.
- When you send or submit something yourself, record it with `jobdb.py stage` as usual - the agent sees it.
- Writing reviewer sub-agent: `agent_app/reviewer.py` with knowledge base `agent_app/reviewer_kb/` (Japanese grammar &
  keigo, English grammar, writing principles). E-mails queued and documents saved by the GUI agent are reviewed
  automatically (setting `review_mode`: off / suggest / auto). When you write an important text yourself, you can
  run `reviewer.check({"body": text}, "email", company_id=…)` and apply its fact / keigo findings before sending.
- Company intelligence (RAG): `python -m agent_app.intel search "<query in any language>" [--contacted no] [--company <id>]`
  finds companies by meaning and recalls what is known about one; `python -m agent_app.intel company <id>` re-scrapes
  and re-indexes one company. Database descriptions can be stale (a company may have pivoted or sold a business): check the live site before
  writing. Changes you record with `jobdb.py` mark the company for re-indexing automatically; if the GUI is not
  running, `python -m agent_app.intel dirty` processes them.
- Notes live in table `notes` (kind `study` / `interview` / `todo`, optional `company_id`, markdown `body`,
  `status` open/done, `due`). The GUI shows an icon on kanban cards that have open study notes or an interview
  note, and the company drawer renders them. Write them through `agent_app.store.save_note(kind, title, body,
  company_id, status, due)` (same kind+company+title updates in place): add an interview note whenever an
  interview is booked, a study note for coding tests / problem sets / topics to learn, mark study notes done
  when finished, and keep the single `todo` note current.

## Start of every task

0. `python jobdb.py todo` — open questions waiting for the user (table `open_items`). If the user's
   message answers any of them, record it with `python jobdb.py answer <id> "<answer>"`, apply it to the
   profile/documents, and regenerate affected documents. When you need new information from the user,
   log it with `python jobdb.py ask "<question>" --topic ... --for ... [--priority high]`.
1. `python jobdb.py profile` — load the candidate's structured profile. Treat it and `profile/profile.md` as
   the only source of facts about the candidate. If something needed is missing, ask; in drafts use a
   visible `[placeholder]`.
2. If the task concerns specific companies, `python jobdb.py show <id>` (add `--full` for all scraped text).
   Find ids with `python jobdb.py search "<words>"`.

## Workflows

### A. Find and rank companies

1. `python jobdb.py prerank --unscored --limit 60` gives a free keyword ranking (region defaults to
   `japan`; `--region any` for all). It is only a filter — it misses companies whose websites are thin.
   Also skim relevant sectors with `python jobdb.py search "" --sector materials --region japan --limit 50`.
2. Read compact cards in batches: `python jobdb.py cards <id> <id> ... --chars 600`. Output can be large;
   batch 15–25 ids at a time.
3. For promising companies, look at the live careers page / ATS board (HRMOS, HERP, Talentio, Greenhouse,
   Lever, Ashby...). Scraped careers text is often just navigation; the real job list is usually one click
   deeper. Fetch it (WebFetch, or a short `requests` + BeautifulSoup script) and note concrete open roles,
   location, required language and requirements.
4. Score using `agent_app/kb/scoring.md`, calibrated against the anchors in `资料/knowledge.md`. Write a JSON list to `data/scores_<date>.json`
   (`[{id, score, roles[], reasons[], concerns[]}]`, English, reasons citing concrete facts) and store it
   with `python jobdb.py set-scores data/scores_<date>.json`. Then `python jobdb.py ranking` and
   `python jobdb.py export`.
5. Report to the user in Chinese: a short ranked table (score, company, best-fit role, one-line why, main
   risk) and a recommended next action for the top 3–5.

### B. Deep-dive one company

Read `jobdb.py show <id> --full`, fetch the careers board and each relevant job posting, and web-search
recent news (funding, products, hiring, English usage, office location, visa sponsorship history). Save
a research note with `save-draft --kind company_research` so it is reusable, and update the score if the
picture changed. Clearly separate verified facts (with URL) from inference.

### C. Draft communication with a company

Read `agent_app/kb/outreach.md` and the personal writing rules in `资料/knowledge.md` first. Decide the channel: prefer the official ATS/job posting; a cold
email only to an address the company publishes (`contact_emails` or its site), or via a warm route the
user names. Write the body to a temp file, then:

```
python jobdb.py save-draft <id> --kind cold_email|cover_letter|reply|follow_up|application_answers|interview_prep --lang ja|en|zh --subject "..." --body-file <tmp> [--to <address or URL>]
```

Show the draft to the user in the chat as well. Tell the user where the file is.

**Gmail connector (preferred)** — if the user's job-search mailbox is connected as a Gmail
connector, Use `search_threads` / `get_thread` at the start of job-search tasks to check for company
replies (search by company domain/name, `newer_than:`), summarise them in Chinese and update the
pipeline. Send with `send_message` only after the user explicitly approves that specific message; then
record it with `python send_mail.py log <mail file> --message-id <gmail id>`. Prefer `create_draft`
when the user wants to review in Gmail first.

**Sending e-mail (fallback)** — `send_mail.py` (SMTP from the user's own address; password kept in Windows
Credential Manager, set by the user via `python send_mail.py setup` — never ask for or handle it).
Put each message in `outbox/mail/<name>.md` (header: to / cc / subject / company_id / attachments /
pdf: yes), then `python send_mail.py preview <file>`. It refuses to send while placeholders
(【要記入】, [TO FILL] …) remain in the text or attachments. Only run
`python send_mail.py send <file> --confirm` after the user has explicitly approved **that specific
message** in chat; it logs to `mail_log`, archives an .eml in `outbox/sent/`, and sets the pipeline
stage to sent. Web forms: fill and submit only with the user's explicit go-ahead; stop at CAPTCHAs,
account creation or passwords and hand over to the user.

### D. Company replied / interview

When the user pastes a message from a company: summarise it in Chinese, log it with
`python jobdb.py stage <id> replied --note "..."`, then draft the reply (workflow C, `--kind reply`).
For interviews, create `--kind interview_prep` with: company/role recap, likely questions (research,
current work, why startup, why this company, visa/start date), talking points mapped to the profile's
unique selling points, questions to ask them, and a 1-minute self-introduction in the interview language.

### Archiving application materials

Every document you produce for the user (CV, 履歴書・職務経歴書, cover letter, form message, strategy
note, interview prep) is registered in the `documents` table so it is findable and its gaps are tracked:

```
python jobdb.py archive <path> --kind rirekisho|cv|form_message|cover_letter|strategy|interview_prep [--company <id>] --status draft|needs_info|final|submitted [--missing "a|b"] --title "..." --lang ja [--generator "<command that rebuilds it>"]
python jobdb.py docs [--company <id>] [--status needs_info]
```

Re-run `archive` on the same path after regenerating (it upserts and re-extracts the text). Documents
built by scripts: the generator scripts in `资料/profile/` (e.g. `make_rirekisho.py`, `make_resume_en.py`;
fields not in the profile go in `资料/profile/rirekisho_fields.json`). Take the applicant's name and its readings from the profile; never send the raw
template in `资料/profile/materials/`.

### E. Track progress

`python jobdb.py pipeline` shows the latest stage per company. Stages: shortlisted → drafted → sent →
replied → interview → offer / rejected / closed. Whenever the user reports progress ("发了", "约了面试",
"被拒了"), record it with `python jobdb.py stage <id> <stage> --note "..."`. When asked for a status
overview, also flag follow-ups due (sent ≥ 7 days ago with no reply).

### F. Update the profile

When the user gives new facts or materials: edit `profile/profile.md` (keep its structure, Chinese),
copy new files into `profile/materials/`, run `python jobdb.py ingest`, then update the structured
profile: dump it with `python jobdb.py profile`, edit the JSON (English), and store it with
`python jobdb.py set-profile <file>`. Keep `open_questions` current.

### G. Company universe, classification, adding sources

The `companies` table holds only **class A** Japanese startups (not IPO'd, not acquired) that publish
at least one contact channel (e-mail, phone or contact-form page) — the user asked to exclude class B
entirely, so don't recommend or re-add listed/acquired companies. Exception: rows with
`tier='backup'` form a separate 保底候选 list the user explicitly asked for;
they are excluded from rankings/statistics and never pruned. Add to it only when the user asks. Current sources: `globalbrains` (VC portfolio), `jstartup` (METI
J-Startup), `meti_univ` (METI 大学発ベンチャーDB, has phone/e-mail/法人番号). `sources` lists every
source a company appears in; duplicates are merged by 法人番号 → domain → normalised name
(`scrapers/common.py: upsert_company`).

Classification (`python classify.py`, columns `category`, `types`, with `*_basis` explaining why):
- `category` A = neither IPO nor M&A, B = IPO or M&A (source status, JPX listed-company file, or
  acquisition wording on the company site).
- `types` `1` = chemistry/materials, `2` = IT, `1,2` = both, `other` = neither.
Filter with SQL or `python jobdb.py search ... ` (e.g. category A + type 1 = unlisted chem/materials
startups). Rules are keyword-based: when a label looks wrong, correct the row by hand and mention it.

To add a source: write `scrapers/<source>.py` that builds field dicts and calls
`upsert_company(conn, "<source>", <id>, fields)`; run it, then
`python scrapers/enrich.py --region japan` (fetches new sites: description, careers page, e-mails,
phone, contact form), then `python classify.py --prune` (classifies, then drops companies outside Japan, without any contact,
or in class B, keeping only rows referenced by the pipeline or documents). Inspect the target page
first — embedded JSON (`__NUXT_DATA__`, `__NEXT_DATA__`) or official Excel downloads beat HTML parsing.

## Candidate facts that shape every judgement

Read them from `资料/profile/profile.md` and `python jobdb.py profile` at the start of each task; typical
deciding factors are residence status and visa support (e.g. a change from 留学 to 技術・人文知識・国際業務,
part-time limited to 28 h/week before graduation), preferred location and working language, role
preference order, and anything the user has said not to consider. Don't invent facts or salary expectations
that the profile does not state.
