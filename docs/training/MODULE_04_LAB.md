# Training Lab — Safe OpenAPI References

## Goal

Understand reusable schemas, deterministic composition, and the security risks created by unrestricted reference resolution.

## Lab

1. Create `components.schemas.Identity` with a required integer `id`.
2. Create `components.schemas.User` using `allOf` with Identity and a required email property.
3. Reference User from a POST request body.
4. Run `specvora analyze` and inspect `request-cases.json`.
5. Change the reference to `https://example.com/user.json` and confirm analysis stops.
6. Create a circular A-to-B-to-A reference and inspect the explicit chain error.

## Review questions

- Why are remote references rejected even when the URL uses HTTPS?
- What evidence is lost if a resolver silently chooses a union variant?
- How does fail-closed behavior preserve human authority?
