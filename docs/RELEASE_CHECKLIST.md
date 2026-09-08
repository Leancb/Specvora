# Release checklist — v0.1.0

## Automated evidence

- [x] Full Pytest suite passes on Python 3.12.
- [x] Ruff passes for `src` and `tests`.
- [x] Editable installation succeeds in the maintained development environment.
- [x] Continuous Quality workflow is configured for `main` pushes and pull requests.
- [x] Governed fixture workflow remains separately protected and manually authorized.

## Release integrity

- [x] Package and changelog versions are `0.1.0`.
- [x] Repository contains no generated local keys, runtime tokens or private approvals.
- [x] Working tree is clean before tagging.
- [ ] Wheel build succeeds in the Quality workflow's network-enabled runner.
- [ ] Quality workflow succeeds for the exact release commit on GitHub.
- [ ] Create annotated tag `v0.1.0` only after reviewing the exact commit SHA.
- [ ] Push the tag and publish release notes from `CHANGELOG.md`.

## Declared boundary

This checklist closes the training MVP, not a production deployment. Do not expose the portal or
state service to a network until operated TLS, distributed storage, workload identity, secrets
management, backup/recovery, retention and security ownership are established.
