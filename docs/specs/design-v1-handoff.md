# Handoff: Trusted Installer Corpus — v1 Implementation Planning

## Focus for next session

Take the approved v1 design spec and produce a concrete implementation plan
(task breakdown) for a coding agent to execute. No code has been written yet.

## Current state

- Project: **Trusted Installer Corpus** — dataset of legitimate installer
  URLs, built by measuring how widely each URL is referenced across GitHub
  (occurrence count, unique repos, unique owners, star signal). Used to help
  security tools distinguish trusted install commands (`curl ... | bash`)
  from suspicious ones.
- We went through a full brainstorming pass (approaches compared, questions
  answered) and landed on a v1 design: seed-list-driven, exact-match GitHub
  Code Search per URL — not broad pattern/regex crawling (confirmed GitHub's
  REST Code Search API does not support regex, only the cs.github.com web UI
  does).
- **Design spec is written and committed**:
  `docs/specs/design-v1.md`
  This is the source of truth for architecture, schema, data flow, error
  handling, and test strategy. Read it before doing anything else — do not
  re-derive these decisions from this handoff doc.
- Spec status: written and committed to git, presented to the user for
  review. **User had not yet confirmed approval when this session ended** —
  confirm the spec is still accepted before generating the task plan, in
  case they requested changes after this handoff was written.

## Key decisions already made (don't re-litigate without reason)

- Stack: Python (requests + PyGithub)
- Auth: shell out to `gh auth token` (user has gh CLI authenticated, no
  separate PAT)
- Storage: SQLite for pipeline state + JSON export for consumers
- Seed list: manual core list (~50-100) + scraped from curated lists
  (awesome-cli, webinstall.dev), combined into `seed_list.json`
- Execution: local script, manual run — no CI/scheduling in v1
- Metadata scope: minimal (occurrences, unique repos/owners, stars) —
  verified-org status, activity signals, domain reputation deferred to v2
- Crawl method: per-seed-URL exact Code Search query, not broad
  pattern/regex search (API limitation, see spec)

Full rationale and trade-offs for these are in the spec doc — don't
duplicate them here, just don't casually override them.

## Suggested skills for next session

- **writing-plans** (if available in that environment) — this is the
  designated next step per the brainstorming skill's process; use it to
  turn the approved spec into a task-by-task implementation plan.
- **brainstorming** — only re-invoke if the user wants to change scope or
  the spec gets rejected wholesale; otherwise skip, brainstorming is done.
- Standard coding skills (repo setup, testing) as needed once task planning
  starts — no framework-specific skill needed, this is a plain Python
  script pipeline.

## Open items for next session to resolve

- Confirm user's final sign-off on the spec (or capture requested edits).
- Decide where in the repo the scraped seed-list sources (awesome-cli,
  webinstall.dev parsing) live — spec defines the combined output format
  but not the scraper implementation details.
- No API keys, tokens, or secrets were shared or embedded anywhere in this
  session — auth is entirely via local `gh auth token` shell-out at
  runtime.
