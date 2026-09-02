# Module 07 — Complete Union Variant Cases

## Objective

Generate transparent request-data cases for every `oneOf` and `anyOf` alternative instead of silently selecting one schema.

## Behavior

- internal references inside union alternatives are resolved first;
- union arrays remain visible in the quality plan;
- each alternative receives a numbered valid case;
- required-field omissions and supported boundary violations are generated per alternative;
- required parameter omissions remain independent and use the first variant only, avoiding combinatorial duplication;
- nested unions use the first alternative only when producing a value inside a larger schema and remain identified in the schema metadata.

Case IDs include their origin, such as `createPayment-valid-oneOf-1` and `createContact-valid-anyOf-2`.

## Additional constraints

This module adds deterministic handling for `maxLength`, `maximum`, `minItems`, and `maxItems`, extending the existing `minLength`, `minimum`, and enum coverage.

## Design boundary

For `oneOf`, generated values are proposals and are not yet checked for exclusive validity against all alternatives. For `anyOf`, combinations of multiple alternatives are not generated. A future schema validator can prove compatibility and eliminate overlapping or impossible cases.

## Demonstration

1. Define email and phone schemas under `components`.
2. Reference both from an `anyOf` request body.
3. Run `specvora analyze`.
4. Show two numbered valid cases and their independent negative cases in `request-cases.json`.
