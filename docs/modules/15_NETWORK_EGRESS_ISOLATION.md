# Module 15 — Container and OS network egress isolation

## Outcome

Specvora can create an immutable Linux network policy for one approved HTTP(S) target. The
policy records the normalized hostname, TCP port, resolved IPv4/IPv6 addresses, creation time,
human authority, and SHA-256 of a deterministic `nftables` ruleset.

The ruleset drops output by default and permits only established traffic plus TCP connections
to the pinned addresses and port. It permits neither DNS nor arbitrary UDP. This complements,
and does not replace, the application allowlist and explicit test-execution approval.

## Fail-closed controls

- exact token `APPROVED_EGRESS_POLICY`;
- exact host membership in the supplied allowlist;
- HTTP/HTTPS target and explicit or scheme-default port;
- successful address resolution before policy creation;
- confined and immutable policy directory;
- canonical cross-platform rule bytes bound by SHA-256;
- deterministic reconstruction during verification;
- container entrypoint validates and applies rules before reducing privileges.

## Runtime boundary

`deploy/egress/Dockerfile` installs `nftables` and `setpriv`. The entrypoint requires the
approved rules at `/policy/specvora-egress.nft`, checks their syntax, applies them, changes to
the unprivileged `nobody` identity, enables `no-new-privileges`, and removes every capability
from the bounding set before the test process starts.

The operator must launch with a normal isolated Docker bridge, `--cap-drop ALL` followed by
`--cap-add NET_ADMIN`, a read-only policy mount, and `--add-host` entries matching the policy.
Never combine this profile with `--network host`, privileged mode, extra capabilities, or a
writable policy mount.

## Limitations

This repository validates policy generation and container configuration deterministically.
Actual firewall enforcement depends on a Linux kernel/container runtime and must be exercised
in the deployment environment. Address rotation requires a new approval and policy; silently
re-resolving during a run would weaken protection against DNS rebinding.
The SHA-256 link detects accidental or one-sided rule changes but is not a signature; signed
approval records remain a separate roadmap control.
