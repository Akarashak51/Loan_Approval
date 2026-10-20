# Frontend Tests

Uses [Vitest](https://vitest.dev) + `@testing-library/react`. Run with:

    cd frontend
    npm install
    npm run test

`featureConfig.test.ts` verifies the form-driving feature config stays
consistent (every field has a label, protected attributes stay
immutable, numeric fields have ranges) -- this is what the Application
form and validation logic depend on.

Component-level tests (form validation, API integration mocking,
result rendering) are added incrementally as pages stabilize; see
spec section 40 for the target coverage (form validation, API
integration, result rendering).
