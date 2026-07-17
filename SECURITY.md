# Security Policy

## Supported Versions

This project is in early/active development. Security fixes are applied to the latest
release on the `main` branch only.

## Reporting a Vulnerability

If you discover a security vulnerability, **please do not open a public GitHub issue**.

Instead, report it privately:

1. Go to the repository's **Security** tab and use **"Report a vulnerability"**
   (GitHub's private vulnerability reporting), or
2. Open a private security advisory.

Please include:
- A description of the issue and its potential impact.
- Steps to reproduce, including any proof-of-concept.
- The affected version/commit.

We will acknowledge reports promptly and aim to respond with an initial assessment
within a reasonable timeframe. Coordinated disclosure is appreciated.

## Responsible Use

Ghost Agent automates browser interactions with third-party job platforms and
messaging services. Users are solely responsible for ensuring their use complies with:

- The Terms of Service of every platform they interact with.
- All applicable local, regional, and national laws and regulations.
- Anti-spam and electronic-communications regulations (e.g. CAN-SPAM, GDPR, IT Rules).

The maintainers do not endorse automated messaging that violates any platform's terms
or any law. Misuse is the sole responsibility of the user.

## Secret Hygiene

- Never commit real API keys, bot tokens, passwords, cookies, or resumes to this
  repository.
- All secrets must live in your local `.env` file, which is git-ignored.
- Browser session profiles, databases, and logs are git-ignored and must never be
  committed.
- If you accidentally commit a secret, rotate it immediately — assume it is
  compromised. Do not rely on simply removing it from history.
