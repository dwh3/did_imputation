# Security Policy

## Supported Versions

didimpute v0.1 targets Python 3.9+ and assumes reproducible workloads with deterministic seeds. Future releases will continue to support the latest 3 Python minor versions.

## Reporting a Vulnerability

Report potential vulnerabilities, data-handling issues, or parity regressions by opening a private security advisory or emailing security@example.org. Please include:

- didimpute version (`python -m didimpute --version` or `python -m pip show didimpute`)
- Python version and OS
- Minimal reproducible example or traceback

We acknowledge reports within five business days and aim to provide fixes or remediation timelines within 21 days.

## Data Handling Expectations

- No personally identifiable information (PII) is required; all tests rely on synthetic, seeded data.
- The estimator pipeline is deterministic given the same inputs (seeds 100–149 in parity simulations); randomness is reserved for future bootstrap extensions.
- CLI file paths and output destinations are user-specified, and the project does not transmit data externally.

## Disclosure Policy

We follow coordinated disclosure: please give us an opportunity to address issues before public disclosure. Credit is given to reporters in release notes unless anonymity is requested.
