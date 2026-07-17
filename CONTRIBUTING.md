# Contributing to Ghost Agent

Thanks for your interest in improving Ghost Agent. This document explains how to
contribute safely and effectively.

## Before You Start

- This is an open-source project. **Never commit secrets, personal data, real
  resumes, cookies, sessions, or database files.** The `.gitignore` already excludes
  `.env`, `data/web_session/`, SQLite databases, and logs.
- By contributing, you agree that your contributions are licensed under the project's
  [MIT License](./LICENSE).

## Development Setup

1. Fork and clone the repository.
2. Create and activate a virtual environment:
   - Windows: `python -m venv ghost_env` then `ghost_env\Scripts\activate.bat`
   - Linux/macOS: `python3 -m venv ghost_env` then `source ghost_env/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Install the browser: `playwright install chromium`
5. Copy `.env.example` to `.env` and fill in your own values (do not commit `.env`).
6. Put your resume at `data/master_resume.txt` (a sample template is provided).

Convenience scripts are provided in `scripts/` (`setup_<os>` and `run_<os>`).

## Code Style

- Keep it simple and small. Prefer the standard library and existing helpers over
  new dependencies or abstractions.
- Match the existing code style and naming conventions.
- Do not add comments unless a non-obvious shortcut or ceiling needs documenting
  (use a `ponytail:` comment for deliberate simplifications).
- Keep functions focused; reuse helpers that already exist in the codebase.

## Scope of Changes

- Naukri is the currently supported platform. Improvements to Naukri scraping are
  welcome.
- Support for Glassdoor, Indeed, and Foundit exists but is incomplete. If you work on
  these platforms, clearly mark the status so it is not mistaken for production-ready.

## Submitting Changes

1. Create a focused branch: `git checkout -b fix/short-description`.
2. Make minimal, well-scoped commits with clear messages.
3. Test your change locally (at least a syntax/import check: `python -c "import main"`).
4. Ensure no secret or local artifact is staged:
   `git status` and `git diff --cached` should contain no `.env`, no `data/web_session/`,
   no `.db`, and no real personal data.
5. Open a pull request describing what changed, why, and how it was tested.

## Reporting Issues

When filing an issue, include:
- Platform and OS you used.
- Steps to reproduce.
- Expected vs. actual behavior.
- Relevant logs **with all personal data redacted**.

## Security Reports

Do not file security issues publicly. See [SECURITY.md](./SECURITY.md).
