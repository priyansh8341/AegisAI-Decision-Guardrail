# AegisAI 2.1 - start here

A finished local portfolio release for structured decision review. It demonstrates typed LLM output, deterministic policy scoring, local persistence, failure handling, evaluations and human review. It does not provide validated risk predictions or production access controls.

## Run the existing restored project

In PowerShell inside this folder:

```powershell
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8001
```

Open http://127.0.0.1:8001. If an older server is running in another terminal, stop it with Ctrl+C first so the new code loads. Keep Ollama running. Your existing database stays at data/aegis.db.

## On another Windows computer

Python 3.11.9 was used for this release's checks. Install Python and Ollama from their official vendors. From the extracted folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
ollama pull llama3.2:3b
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8001
```

The lock records this machine's tested environment, including test dependencies. It has not been verified on other operating systems/Python versions. The original virtual environment and downloaded model are not transferred. Extract into a NEW folder; do not overwrite another database. The full transfer archive contains saved assessment data and is intended for your own use, not public repository upload.

## A three-minute demo

1. Choose Explore samples. Run the database-migration scenario and explain the risk register and deterministic priority formula. Samples are fixed fixtures, not model results.
2. Open Human review. Record a revision request with a reason; inspect its persisted audit entry.
3. Export Markdown and JSON. Reopen the report from Assessment library and compare two samples.
4. Switch to live mode, enter your own brief and constraints, and run it with Ollama. Generation may take up to three minutes.
5. Read the source brief, check claims/contradictions and practical mitigations. Complete the three checklist acknowledgements before an approval; the app records your acknowledgement, not proof of correctness.
6. Show evaluation/RELEASE_RESULTS.md and explain validity versus answer quality, a contradiction, and why the attempted self-review feature was disabled by default.

## Evidence and learning

- evaluation/RELEASE_RESULTS.md: final release measurements and limitations.
- evaluation/VALIDATION_REVIEW.md: 14/20 to 20/20 validation iteration.
- evaluation/runs/20261021T123220094566Z/assistant_quality_review.csv: single-rater AI-assisted review of 20 development answers; not independent human labels.
- evaluation/README.md: dataset, rubric, reproduction commands and historical experiments.
- ARCHITECTURE.md: implementation and tradeoffs.
- PORTFOLIO.md: accurate project description and interview talking points.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe evaluate.py --check --split all
```

All tests use simulated model calls and isolated databases. The dataset check makes no model calls. Held-out results are a one-time evaluation, not another tuning dataset. The experimental automated reviewer is disabled: AEGIS_ENABLE_REVIEW defaults to 0. Enabling it adds a second request and does not establish safety or accuracy.
