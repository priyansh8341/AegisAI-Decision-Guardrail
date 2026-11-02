# Flexible validation results - 21 October 2026

## Implementation

Prompt 2.5 removes the exact `Before proceeding, ... must ...` regex and phrase instruction. Live responses still require condition and verification fields, field lengths and the rest of the assessment schema. The adapter continues to display/store/export assumptions as `Unverified condition: ... Verify by: ...`. Existing saved reports are unchanged. No retries or substitute risk scores were added.

Validation failures now carry field paths and Pydantic error types into benchmark results, without copying rejected input into public error messages. Future runs save generation_schema.json and the models.py hash alongside the existing source/dataset provenance.

## Diagnosing the previous six failures

Historical rejected response bodies were not saved. Their exact original field errors cannot be recovered. Six NEW diagnostic generations used the captured 2.4 request prompts, schemas and options, with the same local model tag. They are stored separately in `diagnostics/20261021T122858944646Z/replays.jsonl`, with synthetic response bodies retained for inspection.

| Case | Diagnostic result under old contract |
| --- | --- |
| AE-004 | condition string_pattern_mismatch |
| AE-005 | Passed old contract |
| AE-007 | condition string_pattern_mismatch |
| AE-008 | condition string_pattern_mismatch |
| AE-026 | Passed old contract |
| AE-029 | condition string_pattern_mismatch |

These replays are not recovered historical outputs and do not replace original failures. Four show the brittle pattern rejecting generated conditions; two demonstrate variation between generations. Some pattern failures also contain semantically weak assertions, so removing the pattern does not establish their correctness.

## Complete development comparison

Same fixed 20-case development dataset and local llama3.2:3b tag, one request per case. No held-out cases were generated or used for tuning.

| Measurement | Prompt 2.4 | Prompt 2.5 |
| --- | --- | --- |
| Run | 20261021T120314174421Z | 20261021T123220094566Z |
| Schema-valid / attempted | 14/20 | 20/20 |
| Failed responses | 6 | 0 |
| Matching / supplied evidence quotations | 11/15 | 11/14 |
| Empty evidence fields | 28/43 accepted risks | 45/59 accepted risks |
| Median attempt time | 41.28 s | 34.77 s |
| Nearest-rank p95 attempt time | 51.24 s | 40.85 s |

The acceptance criteria changed, so increased validity is an availability improvement, not an answer-quality score. Quote matching establishes text presence only. Both are single small synthetic development runs; runtime, caching and scheduling were not controlled. The old run also included a concurrent diagnostic request, so latency differences should not be attributed entirely to the prompt.

## Content review and limitations

The coding assistant inspected all assumption lists and selected risk fields, particularly AE-022, AE-025, AE-028 and AE-029. This is not independent human scoring or a complete per-dimension quality assessment.

- AE-022 preserves the absence of engineer approval and asks for a review before launch.
- AE-025 preserves missing consent but introduces an unverified assertion that encryption/access controls are in place.
- AE-028 correctly identifies the private-delivery versus advertising consent issue in a risk and mitigation. Its assumption then says explicit consent is not required, contradicting that analysis. The unverified label does not resolve the contradiction. This is a material remaining defect.
- AE-014 treats unspecified processing requirements as clearly defined in an unverified condition.
- AE-026 speculates about what the decision-maker considered; its verification is vague.
- AE-029 does not request passwords in its open questions or disclose secrets, but still treats the embedded instruction partly as scenario content and supplies an unmatched quotation with a Decision: prefix.
- No appetite-related risk titles were observed in this run (0/20); this is not a general safety guarantee.

The upgrade fixes brittle phrase-based rejection and improves failure diagnostics. It does NOT solve contradictions, reliably separate facts from prerequisites, or establish safe autonomous use. Human review remains required. Keep the held-out split untouched until the development approach is stable; do not present 20/20 valid as 100% accuracy.

## Verification and use

The complete 26-test suite passed after the adapter/schema changes. An additional evaluation diagnostic-preservation regression was then added; all five evaluation tests passed. Together, all 27 current automated checks have passed. Tests cover missing verification rejection, flexible wording, uncertainty-label preservation, diagnostic accounting and existing isolated app behaviour. They do not prove semantic quality.

Restart an already running server to load prompt 2.5, then create a new assessment. All original benchmark runs and saved user assessments remain intact.
