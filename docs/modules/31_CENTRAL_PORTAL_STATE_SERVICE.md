# Module 31 — Central portal state service

Module 31 supplies the service required by the Module 30 HTTP adapter. It exposes the existing
portal-state contract through a dedicated FastAPI application backed by transactional SQLite:
atomic MFA counter claims, session registration, active-session lookup and revocation.

Run the service separately from the review portal. Configure `SPECVORA_STATE_SERVICE_DB` and
inject a bearer value through `SPECVORA_STATE_SERVICE_TOKEN`; the token must contain at least
32 characters. `/health` is intentionally unauthenticated, while every state operation fails
closed without the exact bearer credential. Interactive API documentation is disabled.

The service preserves the single-host SQLite guarantees from Module 28. It is suitable for local
integration and controlled training, but it is not a production multi-node datastore. Production
deployment still requires TLS termination, workload identity or managed token rotation, tenant
isolation, rate limiting, monitoring, backups and an externally operated transactional database.

The browser portal never receives the service token. Only the server-side HTTP adapter calls this
service, and offline signatures remain an independent requirement for governed actions.
