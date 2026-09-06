# Module 33 — Transactional portal login throttling

Module 33 adds a fixed authentication budget of five attempts per normalized username hash in a
five-minute window. The claim occurs before password hashing and covers password and TOTP
failures. A complete successful authentication clears the subject's window.

The state contract now exposes atomic attempt claim and reset operations. SQLite uses an
immediate transaction; the central service exposes matching authenticated endpoints, and the
HTTPS adapter validates only the expected `201`, `204` and `429` outcomes. Raw usernames and
passwords are never stored in the throttle table.

All authentication failures keep the existing generic message. This reduces online guessing and
expensive password-hash abuse without revealing whether an account exists. It does not replace
edge rate limiting by source/network, abuse monitoring, external identity risk signals or an
operated distributed datastore.
