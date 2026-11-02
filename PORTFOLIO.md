# Portfolio description

## Suggested project entry

**AegisAI - Local LLM Decision Review Workspace**

Python, FastAPI, Pydantic, SQLite, Ollama, JavaScript

- Built a structured LLM workflow with independent output validation, deterministic risk prioritisation, saved reports, comparison and Markdown/JSON exports.
- Developed a 30-case synthetic benchmark with fixed development/held-out splits, failure accounting, latency measurements, source quotation checks and a documented quality rubric.
- Investigated prompt/schema failures, replacing brittle phrase validation while preserving explicit uncertainty labels and reproducible evaluation evidence.
- Implemented human-review notes, server-enforced approval checklist acknowledgements, version conflict protection and persistent review history.

Only add benchmark numbers after checking RELEASE_RESULTS.md. Schema-valid output is not answer accuracy. Do not claim production deployment, calibrated risk predictions, independent human evaluation, external approval enforcement or reliable automated contradiction detection.

## Interview discussion

Explain why policy metadata was removed from model input; why parseable JSON is insufficient; how strict wording reduced availability; why a second LLM review pass was left disabled after disappointing results; how failed attempts and human review are preserved; and what a stronger model/independent evaluation would need to establish.

Show working code and synthetic examples. Distinguish personal implementation knowledge from assisted work and be able to explain and modify each module you present.
