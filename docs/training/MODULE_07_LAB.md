# Training Lab — oneOf and anyOf Coverage

## Goal

Understand the difference between union semantics and verify that every declared alternative receives visible test-data coverage.

## Lab

1. Create `CardPayment` and `PixPayment` component schemas.
2. Reference both through `oneOf` in a POST request body.
3. Run deterministic analysis twice and compare the case IDs and values.
4. Confirm that both valid variants exist.
5. Confirm that each variant has its own required-field omission.
6. Add `maxLength`, `maximum`, or array limits and inspect the negative boundary case.

## Review questions

- Why can overlapping `oneOf` schemas make a generated value invalid?
- Why does Specvora avoid multiplying parameter omissions by every body variant?
- What extra validator is needed to prove union compatibility rather than merely propose cases?
