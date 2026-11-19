# Security policy

## Supported versions

This project is experimental. Security fixes target the current `main` branch.

## Reporting a vulnerability

Do not publish credentials, API keys, tokens or exploit details in a public issue.
Open a private report to the repository maintainer with:

- affected commit or version;
- reproduction steps;
- impact;
- suggested mitigation, if available.

Immediately revoke any credential that may have appeared in a task output, log, commit or report.

Coding Harness is not yet a production sandbox. Its current path validation is primarily a policy and post-execution control; do not use it as a security boundary for untrusted code.
