# Module 04 — Safe Schema References and Composition

## Objective

Resolve reusable OpenAPI schemas without allowing the contract to fetch network resources or read arbitrary files.

## Supported behavior

- internal JSON Pointer references beginning with `#/`;
- escaped JSON Pointer tokens `~0` and `~1`;
- sibling constraints extending a referenced dictionary;
- recursive resolution through parameters and request bodies;
- `allOf` composition with merged properties and required fields;
- deterministic first-variant selection for `oneOf` and `anyOf`;
- stable examples for email, UUID, date, date-time, hostname, IPv4, and URI formats.

## Security boundary

HTTP URLs, file URLs, relative files, missing pointers, and circular reference chains are rejected. This prevents schema ingestion from becoming an SSRF or arbitrary-file-reading path.

Selecting the first union variant is a documented proposal policy, not proof that other variants are tested. Future work will emit a case for every compatible variant.

## Demonstration narrative

1. Show a reusable `components.schemas.User` definition.
2. Reference it from a request body.
3. Run deterministic analysis.
4. Inspect the resolved valid email and UUID in `request-cases.json`.
5. Replace the internal reference with an HTTPS reference and show fail-closed behavior.

## Acceptance evidence

- references and composition are covered at unit level;
- the full pipeline resolves a component into generated request data;
- remote reference rejection is verified through the public pipeline;
- cycles and missing pointers fail with explicit errors.
