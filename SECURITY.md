# Security Policy

PROXIMUS handles sensitive data — resumes (PII), phone numbers, call transcripts,
and credentials for telephony and AI services. We take security seriously and
appreciate responsible disclosure.

## Supported Versions

This project is pre-1.0. Security fixes are applied to the `main` branch.

## Reporting a Vulnerability

**Please do not open a public issue for security vulnerabilities.**

Instead, report privately via one of:

- GitHub's [private vulnerability reporting](https://github.com/Adawodu/PROXIMUS/security/advisories/new)
- Email the maintainer: see https://adawodu.com

Please include:

- A description of the vulnerability and its impact
- Steps to reproduce (proof of concept if possible)
- Affected version / commit
- Any suggested remediation

We aim to acknowledge reports within a few days and will keep you informed as we
work on a fix.

## Scope & Known Limitations

PROXIMUS is a self-hosted reference implementation. By design (and documented in
the README), it currently:

- Has **no authentication** on the REST API — do not expose it to the public
  internet without your own auth/proxy layer.
- Stores data as **plaintext JSON files** on local disk (`data/`).
- Loads provider credentials from a local `.env` file.

These are operational responsibilities of whoever deploys it. Reports about these
documented limitations are welcome as feature requests, but are not treated as
vulnerabilities unless they describe an exploit beyond the documented behavior.

## Handling Credentials

- Never commit `.env` or real API keys. `.env` is gitignored.
- Rotate any key that may have been exposed.
- The example file `.env.example` contains placeholders only.
