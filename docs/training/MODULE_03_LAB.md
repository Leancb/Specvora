# Training Lab — JSON Schema Test Data

## Goal

Learn how Specvora converts contract constraints into transparent test-data proposals.

## Exercise

1. Add a POST operation to a disposable OpenAPI copy.
2. Define a required `name` with `minLength: 3` and an `age` with `minimum: 18`.
3. Run `specvora analyze`.
4. Predict the valid body before opening `request-cases.json`.
5. Identify the missing-required cases and the boundary violation.
6. Explain why the generated data still requires review and explicit execution approval.

## Expected observations

- valid name is `xxx`;
- valid age is `18`;
- required properties receive separate omission cases;
- the first sorted boundary property receives a deterministic invalid value;
- repeated analysis of the same contract produces the same cases.

## Discussion questions

- What should happen when a schema contains `$ref`?
- Why is deterministic output useful for review and audit?
- Which constraints should be added before supporting production-grade schemas?
