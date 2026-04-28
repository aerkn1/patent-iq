# PatentIQ Documentation Dossier

This dossier is a sectioned documentation set for PatentIQ. It begins with a business and scope framing section, then walks through how the application works end to end across data sourcing, ETL, analytics, machine learning, backend serving, API contracts, and frontend consumption.

The current implementation baseline documented here is:

1. `etl/` for data sourcing, layered processing, model artifacts, semantic assets, and serving snapshot packaging.
2. `backend_v2/` for the FastAPI V2 runtime and page-shaped API contracts.
3. `frontend_v2/` for the Next.js V2 user interface.

Implementation evidence for that runtime boundary is declared in:

- `etl/README.md:1-18`
- `backend_v2/README.md:1-18`
- `frontend_v2/README.md:1-15`

## Table Of Contents

1. [Section 00. Business Definition, Scope, And Evaluation Lens](00-business-definition-and-scope.md)
2. [Section 01. Data Foundation, Sources, And Layered Lineage](01-data-foundation-and-lineage.md)
3. [Section 02. Backend Serving Architecture And API Contracts](02-backend-serving-and-api-contracts.md)
4. [Section 03. Frontend V2 Workspace Architecture And UI Wiring](03-frontend-v2-workspace-architecture-and-ui-wiring.md)
5. [Section 04. Machine Learning And Forecasting Stack](04-machine-learning-and-forecasting-stack.md)
6. [Section 05. Semantic Search, Vector Assets, And Compare Intelligence](05-semantic-search-vector-assets-and-compare-intelligence.md)
7. [Section 06. UI Metric Traceability Matrix](06-ui-metric-traceability-matrix.md)
8. [Section 07. Release Packaging, Auditability, Testing, And Submission Compliance](07-release-packaging-auditability-testing-and-submission-compliance.md)
9. [Section 08. Worked Example Walkthroughs](08-worked-example-walkthroughs.md)

## Recommended Reading Order

1. Start with Section 00 to understand what PatentIQ is, what it is not, and how bounded scope claims should be interpreted.
2. Continue with Section 01 to understand the bounded data universe, raw sources, and why Bronze/Silver/Gold exists in this project.
3. Read the backend/API and frontend sections next to see how Gold marts become page contracts and UI widgets.
4. Read the ML and semantic sections after the data lineage is clear, because both depend on Silver and Gold contracts.
5. Finish with the UI traceability, compliance, and worked-example sections, which tie business-facing screens back to formulas, files, release artifacts, caveat language, and concrete route usage.

## Working Method For This Dossier

Each section will follow the same structure:

1. plain-language explanation first,
2. architecture and lineage second,
3. formulas and algorithm rules third,
4. code evidence and file citations throughout,
5. UI/backend traceability notes where relevant.

This structure is intentional. The project is analytically dense, so the repo should not need to be reverse-engineered from code alone.

## Non-Code Inputs Still Needed To Finalize The Submission Package

The repository already contains the technical evidence required for the first section. The following items are still needed later to complete the full contest submission package:

1. the exact Section 9 evaluation criteria text, so the final dossier can map evidence directly to the judging rubric,
2. the employer and affiliation disclosure text required by the organizers,
3. the final list of prompts, external tools, and third-party services that should be explicitly disclosed in the submission,
4. the final screenshots or demo-flow references the team wants to use while reading the documentation,
5. the final open-source license inventory and dependency disclosure format preferred for the package.

## Draft Status

1. Section 00 is written and code-cited.
2. Section 01 is written and code-cited.
3. Section 02 is written and code-cited.
4. Section 03 is written and code-cited.
5. Section 04 is written and code-cited.
6. Section 05 is written and code-cited.
7. Section 06 is written and code-cited.
8. Section 07 is written and code-cited.
9. Section 08 is written and code-cited as an end-to-end route walkthrough appendix.

## Remaining Appendix Items

The core technical dossier and worked-example appendix are now present. A later documentation pass can still add:

1. a consolidated glossary and acronym index,
2. a single-file code citation index,
3. final employer, affiliation, prompt, and license appendices if a separate submission package is needed.
