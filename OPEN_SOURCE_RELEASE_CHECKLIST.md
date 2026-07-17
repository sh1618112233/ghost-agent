# Open Source Release Checklist

Tracking document for the public GitHub release of Ghost Agent.

## 1. Security
- [x] No real API keys / tokens / passwords in source or config.
- [x] `.env` is git-ignored; `.env.example` uses placeholders only.
- [x] No SSH keys, PEM files, certificates, or service-account credentials present.
- [x] Browser session profiles, cookies, and cache are git-ignored.
- [x] SQLite databases and logs are git-ignored.
- [x] `SECURITY.md` documents private vulnerability reporting.
- [x] Patterns `API_KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `COOKIE`, `SESSION`, `AUTH`,
      `EMAIL`, `PHONE`, `ADDRESS` re-scanned — no real values remain.

## 2. Personal Data
- [x] No real resumes, CVs, or cover letters. `sample_resume.txt` and
      `sample_cover_letter.txt` use fictional data.
- [x] No real recruiter / lead databases. `sample_leads.csv` uses fake data.
- [x] No real names, emails, phone numbers, or addresses. All examples are placeholders
      (`jane.doe@example.com`, `+00 00000 00000`, `910000000001`, `Example Company A`).

## 3. Non-Repository Files
- [x] No virtual environments committed (`.venv/`, `ghost_env/` git-ignored).
- [x] No `node_modules` / build artifacts / compiled files.
- [x] No screenshots, recordings, downloads, or exports.
- [x] No databases or logs committed.
- [x] `.gitignore` is comprehensive and prevents re-committing runtime data.

## 4. Required Open-Source Files
- [x] `README.md`
- [x] `LICENSE` (MIT)
- [x] `CONTRIBUTING.md`
- [x] `SECURITY.md`
- [x] `CODE_OF_CONDUCT.md`
- [x] `CHANGELOG.md`
- [x] `.env.example`
- [x] `sample_resume.txt`, `sample_cover_letter.txt`, `sample_leads.csv`,
      `sample_config.json`
- [x] `OPEN_SOURCE_RELEASE_CHECKLIST.md`
- [x] `PUBLIC_RELEASE_AUDIT.md`

## 5. Developer Experience
- [x] One-command setup per OS: `scripts/setup_<os>.{sh,bat}` and `make setup`.
- [x] One-command run: `scripts/run_<os>.{sh,bat}`, `make telegram`, `make cli`.
- [x] CLI mode works without Telegram.
- [x] Telegram mode optional and documented.
- [x] Output locations documented in README with a table.
- [x] Manual verification instructions provided.
- [x] Quick Start (CLI) and Quick Start (Telegram) included.
- [x] Every environment variable documented.

## 6. Verification Performed
- [x] All Python modules compile (`py_compile`) and import in a clean venv.
- [x] `pip install -r requirements.txt` succeeds.
- [x] DB layer self-test passes (init / insert / dedup / status / CSV export).
- [x] Salary and phone parsers self-test passes.
- [x] `python main.py --help`, `--export`, and `--interactive` flags verified.
- [x] `data/leads.csv` generated with correct header + rows.
- [ ] End-to-end browser scraping NOT executed in this sandbox (no display / no site
      login); verified via import/parse/DB unit checks instead.

## 7. Final Sign-off
See `PUBLIC_RELEASE_AUDIT.md` for the final verdict.
