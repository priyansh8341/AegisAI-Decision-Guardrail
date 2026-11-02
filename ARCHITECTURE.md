# Architecture and tradeoffs

## Request path

Browser brief -> FastAPI input validation -> Ollama schema-constrained generation -> independent Pydantic validation -> explicit unverified condition/check labels -> deterministic scoring -> SQLite -> report -> human review -> appended review entry.

- models.py defines brief, risk, generation and review contracts. Live condition/verification objects map to backward-compatible report strings.
- agent.py sends decision and constraints only, excluding owner and appetite metadata. It rejects malformed outputs instead of inventing scores. Error diagnostics record field paths/types without exposing rejected content in API messages.
- policy.py computes likelihood x impact x 4 and uses the highest risk. Appetite changes the review threshold, not the model's risk ratings. Scores are ordinal priorities, not probabilities.
- store.py persists assessment snapshots and review history. Approval checklist acknowledgements are enforced server-side and appended to review notes. Names are self-entered; acknowledgements are not verified identities or guarantees.
- server.py connects the API and exports. Cross-origin browser writes are rejected. Loopback is the intended deployment boundary.
- static/ uses vanilla JavaScript and text nodes for model content. No frontend build step is required.
- evaluate.py records dataset/source/schema provenance, latency, quotations and failures. review_saved.py separately evaluates an experimental reviewer against saved development outputs.

## Optional experimental review

quality.py calls the same local model to find contradictions and unsupported claims. It validates that finding quotations occur in the named output/source fields. A valid quotation does not prove a finding is correct. Failures are explicitly check_failed, never clean results. Development testing found the reviewer ineffective at detecting known defects, so AEGIS_ENABLE_REVIEW is disabled by default. Its experimental UI/export support remains available for further research; the release makes no automated consistency guarantee.

## Deliberate limits

Single-user local application, without authentication, multi-tenant access control, encryption-at-rest or tamper-proof audit. SQLite suits local persistence; it is not proof of enterprise scalability. Model timeouts/failures remain visible. A small CPU model can be slow and wrong. Quotation matching is only text-presence checking. Assumptions can contradict facts even when labelled unverified. Structured fields, human checklists and tests improve the workflow but do not establish semantic accuracy.

No private data should be used in public portfolio demos. Use the synthetic samples and benchmarks. Uploaded repository source should exclude data/, .venv/ and local evaluation outputs unless explicitly reviewed for sharing.
