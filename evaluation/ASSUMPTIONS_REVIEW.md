# Conditional-assumptions upgrade - 21 October 2026

## Implementation

Prompt 2.4 requires live assumptions to contain a condition matching `Before proceeding, ... must ...` and a verification step. Both are retained as `Unverified condition: ... Verify by: ...` strings in the existing API/storage shape. Supplied facts remain in the submitted brief; generated prerequisites are not verified facts. Original reports and fixed samples remain unchanged. Invalid responses are rejected before scoring, with no automatic retry or invented fallback score.

This is a structural check, not a logical contradiction detector. The prefix can reject reasonable alternative wording, and passing conditions may still be irrelevant or wrong. Verification field length does not prove the check is useful.

## Experiments retained

| Prompt | Run | Outcome |
| --- | --- | --- |
| 2.1 | 20261021T113459451886Z | Previous complete baseline: 20/20 valid under the older contract |
| 2.2 | 20261021T115348657147Z | Stopped after 8 completed attempts: prompt example leaked into unrelated verification |
| 2.3 | 20261021T115911446283Z | Stopped after 6 completed attempts: remaining schema example leaked into a software-release case |
| 2.4 | 20261021T120314174421Z | Complete: 14/20 accepted; 6 rejected |

Partial runs have interrupted summaries and unattempted counts. The final prompt/schema remove domain examples. Dataset and held-out split are unchanged. No failed result was replaced by a successful retry.

## Final development measurements

- Attempts: 20. Valid: 14 (70%). Failures: 6 (`invalid_output`).
- Failed cases: AE-004, AE-005, AE-007, AE-008, AE-026, AE-029.
- Matching evidence quotations: 11/15 non-empty strings (73.3%); 28 empty evidence fields across 43 accepted risks. This is NOT answer accuracy.
- Median attempt latency: 41.28 seconds. Nearest-rank p95: 51.24 seconds.
- All 25 automated tests passed, including legacy/sample compatibility, preservation of condition/check through scoring and rejection of unconditional assumption wording.

The acceptance rate uses a stricter schema than the baseline, so this is not a like-for-like quality score. One extra AE-004 diagnostic call, excluded from counts, failed specifically on the condition pattern. Other failures have generic adapter error categories; their precise field failures were not captured. The diagnostic ran concurrently with part of the benchmark, limiting latency comparisons. This is a small synthetic development experiment, not a controlled performance study.

## Qualitative review

The coding assistant inspected all accepted assumption lists and risk/mitigation text for AE-025 and AE-028. No independent human rubric scores or complete all-field review are claimed.

Improvements observed:

- AE-001 requires completed training and connectivity checks rather than assuming stable connectivity.
- AE-016 requires establishing completed testing rather than assuming testing happened.
- AE-022 requires testing and engineer approval before launch rather than assuming approval exists.
- AE-025 no longer assumes consent; its risk mitigation explicitly requires consent before export.

Remaining weaknesses:

- Verification steps are often generic or restate the requirement rather than define an observable acceptance test.
- AE-028 misses the mismatch between consent for private delivery and advertising use. Its multiple-AI-algorithm suggestion does not establish image accuracy or consent.
- Some prerequisites focus on secondary or speculative concerns.
- Six rejected responses reduce availability. Rejected AE-029 cannot be counted as a successful adversarial answer.

## Status and use

The representation change is implemented and tested. The model is not yet dependable enough to claim contradictions are solved. Keep the held-out split untouched. Next investigate less brittle semantic validation and/or a separate model comparison, reporting coverage, failures and latency. Preserve these failures in portfolio evidence.

Restart the app server to load prompt 2.4 and its schema, then create a new assessment. Old reports retain their original wording. No saved user assessments were rewritten by the tests or evaluations.
