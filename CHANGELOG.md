# AegisAI 2.1.0 - 21 October 2026

- Completed synthetic evaluation workflow with saved schemas, source hashes,
  failure diagnostics, latency accounting and single-rater assistant quality review.
- Added server-enforced live-approval checklist acknowledgement with audit notes.
- Added optional second-pass reviewer with quote provenance validation and
  distinct failed/clean/flagged states. Disabled by default after the development
  experiment missed all seven known material-defect cases.
- Added tested environment lock, startup/demo guide, architecture and portfolio notes.
- 35 automated tests and JavaScript syntax check pass. Browser visual QA was not
  performed because the browser permission gate denied access.

# Evaluation and prompt update - 21 October 2026

## Flexible wording and validation diagnostics (prompt 2.5)

- Removed the exact prerequisite phrase regex; condition/verification objects
  remain required and are still displayed/exported as unverified.
- Added field paths and validation error types to benchmark failures, without
  including rejected input in API error messages.
- Evaluation runs now save generation schemas and model-contract source hashes.
- Added regression coverage for alternative prerequisite wording, missing-check
  diagnostics and preservation of diagnostics in benchmark accounting.
- Replayed six formerly failed development cases separately under captured 2.4
  request configurations: four failed the phrase pattern and two passed. These
  are fresh diagnostic generations, not recovered original responses.

## Conditional assumptions (prompt 2.2)

- Live generation requires condition/verification objects rather than bare assumptions.
- Stored/displayed reports retain compatible strings prefixed Unverified condition,
  with the verification step included. Existing reports and sample fixtures still load.
- Added consent/connectivity examples and explicit comparison against constraints.
- All 24 automated tests pass. Structural validation cannot establish factual consistency;
  live quality results and remaining limitations must be reviewed separately.

Prompt 2.3 removes domain-specific prompt examples after a partial 2.2 run
copied a consent verification step into an unrelated provider-outage case.
The partial run is retained with its interruption reason and unattempted count.
The conditional generation contract remains in place.

Prompt 2.4 also removes the remaining domain example from the schema and requires
prerequisite grammar (`Before proceeding, ... must ...`). All 25 automated tests
pass, including rejection of an unconditional fact as a live prerequisite.

- Added a 30-case synthetic evaluation dataset, fixed development/held-out splits,
  latency and quotation accounting, checkpointed results and a human-review rubric.
- Retained the first development run as the baseline with a qualitative review.
- Updated prompt to decision-review-2.1: excludes owner and policy metadata from
  model-facing scenario data and clarifies assumptions, evidence and untrusted commands.
- Added prompt-boundary regression tests; deterministic policy thresholds remain applied.
- Added httpx2 to development dependencies for the installed Starlette test client.
- All 22 automated tests pass locally. These tests do not establish model quality.

# AegisAI 2.0.0

Local application update, 18 October 2026.

The original prototype has been expanded into a decision-review workspace with
separate frontend, model contract, policy, persistence and API layers.

## Added

- Professional responsive workspace with a navy navigation rail, light report
  surfaces, source-aware risk register and interactive likelihood/impact matrix.
- Separate brief fields for context, constraints, owner, domain and risk appetite.
- Schema-constrained Ollama responses and independent validation.
- Deterministic, documented risk prioritisation and source quotation matching.
- Explicit failure records without substitute risk scores or invented confidence.
- Three clearly labelled offline sample scenarios, restricted to matching briefs.
- Persistent SQLite library, filters, search and comparison of two reports.
- Human review notes, timestamps, review versions and stale-update protection.
- Markdown and JSON exports containing provenance and review history.
- Local API reference, automated tests, setup instructions and learning map.

## Removed or corrected

- The malformed-output fallback no longer assigns MEDIUM/55/0.55.
- A parsed JSON object is no longer assumed to satisfy the application contract.
- Review buttons now store local reviews instead of showing simulation alerts.
- Model-reported confidence and claims of production readiness have been removed.
- No external approval or policy enforcement is claimed.

## Scope

This is local, single-user portfolio software. It has no authenticated users,
tamper-proof audit, external enforcement or calibrated outcome prediction.
The original GitHub repository and Astrix website source were not edited.
