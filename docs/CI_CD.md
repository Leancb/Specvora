# CI/CD

Each analysis produces `github-actions.yml` as a reviewable template. It uses manual dispatch, a repository secret for the base URL, and runs only the generated test file. Copy it into `.github/workflows/` only after reviewing the generated tests and configuring an authorized non-production target.

The committed governed-fixture workflow additionally consumes the signed approval through a
unique Git reference before starting tests. Its `contents: write` permission exists only for
that ledger claim; generated subprocesses receive neither the GitHub token nor signing material.
