# CI/CD

Each analysis produces `github-actions.yml` as a reviewable template. It uses manual dispatch, a repository secret for the base URL, and runs only the generated test file. Copy it into `.github/workflows/` only after reviewing the generated tests and configuring an authorized non-production target.
