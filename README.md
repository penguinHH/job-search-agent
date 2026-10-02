# Job Agent · 求职 Agent · 就活エージェント

A local job-search agent with a web GUI, built for finding a job at Japanese tech startups.
It keeps a database of ~1,500 startups, researches companies, writes application documents in
Chinese / Japanese / English, sends e-mail and fills web application forms **only after you approve**,
reads company replies and tracks every application on a kanban board.

日本のテック系スタートアップ向けの就活エージェント（ローカル Web GUI）。企業DB・調査・中日英の書類作成・
承認制のメール送信／フォーム入力・返信対応・選考管理まで。

## Features
- **Agent chat** – streaming, every tool call visible. 29 tools: company DB search & scoring, web search,
  page reading, document writing, CV PDF generation, e-mail (approval queue), IMAP inbox, browser form filling
  (Playwright, submit buttons need approval), pipeline updates, questions for the user.
- **Three model back-ends**, switchable in the top bar:
  - **Claude subscription** – drives the local Claude Code CLI (`claude -p`); the agent's tools are exposed
    to it through an MCP server (`agent_app/mcp_server.py`).
  - **Claude API** – Anthropic SDK, `claude-opus-5-5`, adaptive thinking, server-side web search.
  - **Open models** – any OpenAI-compatible endpoint (NVIDIA NIM, DeepSeek, OpenRouter, Ollama), run on the
    OpenAI Agents SDK (`agent_app/oa_runner.py`): SDK agent loop with the app's tools, retries, history trimming.
- **Safety gate** – nothing outward happens without you: e-mails wait in *Approvals* (editable), submit buttons
  are queued, CAPTCHAs / logins / passwords are always yours.
- **GUI** – dashboard & funnel, approvals, kanban pipeline (drag to change stage), company DB with detail
  drawer, inbox matched to companies (incl. HERP / HRMOS / Talentio / jobcan notifications), documents,
  profile / open questions / shared knowledge, settings. UI and agent language: 中文 / 日本語 / English.
- **Writing reviewer (sub-agent)** – every e-mail the agent queues and every text document it saves is checked
  by a separate reviewer with its own knowledge base (`agent_app/reviewer_kb/`: Japanese grammar & keigo, English
  grammar, writing principles for e-mails / 履歴書 / CVs / cover letters / form answers) and a fact check against the
  profile. Mode in Settings: off / suggest (you pick which suggestions to apply) / auto (applied directly, undoable).
  The agent can also call `review_text` before filling web forms.
- **Shared rules** – `agent_app/kb/` (outreach rules, fit-scoring rubric) is loaded into every agent conversation
  and used by Claude Code sessions too; personal rules and scoring anchors stay in the data folder's `knowledge.md`.
- **Notes** – study notes (coding tests, problem sets, topics to learn), interview notes (prep, predicted Q&A,
  reverse questions) and a to-do overview. Kanban cards show an icon when a company has open study notes or an
  interview note; the company drawer renders them. The agent reads and writes them (`list_notes` / `get_note` /
  `save_note`).
- **Company data** – scrapers for the Global Brains portfolio, METI J-Startup and the METI university-startup
  DB, website enrichment (careers page, contacts) and A/B (listed/acquired) + type (chem / IT) classification.

## Layout
```
agent_app/      GUI + agent (FastAPI backend, single-page frontend in static/)
  agent.py      agent loop for the three back-ends
  tools.py      the tool set          mcp_server.py  tools over MCP for the Claude CLI
  mailer.py     SMTP / IMAP            browser.py     Playwright form assistant
scrapers/       company sources + website enrichment
classify.py     A/B and type classification       jobdb.py   CLI for the database
send_mail.py    stand-alone mail sender           config.py  paths (code vs. personal data)
资料.example/    template for your personal data folder
```
Everything personal – database, profile, CVs, mails, browser login – lives in a separate data folder
(`资料/`, or set `JOBAGENT_HOME`) that is **not** part of this repository.

## Setup
```bash
pip install -r requirements.txt
cp -r 资料.example 资料          # then edit 资料/owner.json and 资料/profile/profile.md
python scrapers/globalbrains.py && python scrapers/jstartup.py && python scrapers/meti_univ.py
python scrapers/enrich.py --region japan && python classify.py --prune
python -m agent_app             # → http://127.0.0.1:8765
```
In **Settings** choose a back-end (Claude CLI needs Claude Code installed and logged in; the API back-ends need a
key) and add a Gmail **app password** per mail account. Keys and passwords are stored in the OS credential store
(keyring), never in files. CV PDF export uses Microsoft Word (Windows COM); CV generator scripts are yours and are
referenced from `owner.json` → `resume_builds`.

## Requirements
Python 3.11+, Google Chrome (for the form assistant), Windows recommended (Word PDF export).
