# Changelog

All notable changes to Ghost Agent are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-14
First public open-source release.

### Added
- CLI mode (`main.py`) with `--keyword`, `--location`, `--min_salary`, `--sites`,
  `--count`, `--interactive`, and `--export` flags. Interactive prompts for any
  values not supplied on the command line.
- Telegram bot mode (`telegram_agent.py`) with `/hunt`, `/stop`, and `/cancel`
  commands and live log streaming back to the chat.
- Naukri job scraping via Playwright with human-like delays, overlay dismissal,
  salary filtering (minimum LPA), phone / email extraction, and de-duplication.
- Local AI fit-scoring against your resume using an Ollama model
  (`llama3.2:3b` by default) — no external AI API keys required.
- Outreach waterfall: WhatsApp Web messaging when a phone number is available,
  with an SMTP email fallback when only an email address is found.
- Local SQLite lead store (`core/ghost_protocol.db`) with de-duplication and a
  status column tracking each lead's outreach state.
- CSV export of stored leads to `data/leads.csv` (auto-exported after each run and
  on `python main.py --export`).
- Centralized logging to both the console and `logs/ghost_agent.log`.
- One-command setup / run helpers for Windows, Linux, and macOS (`scripts/`)
  plus a `Makefile` for `make setup`, `make cli`, `make telegram`, `make export`.
- Open-source files: `README.md`, `LICENSE` (MIT), `CONTRIBUTING.md`,
  `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.env.example`, and sample data files
  (`sample_resume.txt`, `sample_cover_letter.txt`, `sample_leads.csv`,
  `sample_config.json`).

### Platform Support
- Naukri is fully supported and actively maintained.
- Glassdoor, Indeed, and Foundit scraping code is present but incomplete and
  not production-ready in this release.

### Security
- Secrets and personal data live only in the git-ignored `.env` file.
- Browser session profiles, databases, and logs are git-ignored.
- All committed sample data is fictional.
