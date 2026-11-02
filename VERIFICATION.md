# Verification — 18 October 2026 (Asia/Dubai)

## Passed

- 15 automated behaviour tests using isolated SQLite files and simulated model
  responses. Coverage includes malformed output, invalid ratings, blank input,
  connection failures, timeouts, evidence mismatch, valid live response handling,
  fixed-sample provenance, edited-sample rejection, durable review history,
  stale-review conflicts, failed-review rejection, required review reasoning,
  JSON/Markdown export, missing records and cross-origin browser write rejection.
- JavaScript syntax check with `node --check static/app.js`.
- All referenced HTML stylesheet/script paths resolve locally.
- Health endpoint, local API reference and persisted records after server restart.
- Chromium browser interaction checks: sample creation, stored human review,
  audit timeline, second sample, two-report comparison, empty search, clear search,
  mode/level filters, a clean New Assessment form, risk-matrix filtering,
  Markdown download, keyboard report-tab navigation and model setup dialog.
- Desktop and responsive Chromium layout inspection at widths 1440, 1280, 768,
  390 and 320 pixels. No page-level horizontal overflow in the inspected states.
  Included form, result, risk register, review form, library and explicit failure
  state. Mobile form controls use 16px text; desktop uses a two-column workspace.
- Live loading-to-content transition, with disabled form controls and elapsed time.
- Separate QA instance with a deliberately missing model: failed report shown
  without a risk score or review action. QA data is separate from the main library.
- Two actual local model requests completed and passed output validation:
  - `llama3`: documentation-pilot brief, 118.833 seconds, 3 risks.
  - `llama3.2:3b`: product-release brief, 55.962 seconds, 3 risks.
  Both timings are single observed runs on this computer using CPU inference,
  with different briefs and prompt settings. They are not a comparative benchmark.
  The smaller model is the configurable default for the delivered application.

## Limits

- These checks establish application behaviour, not the correctness of a model's
  risk judgments. No calibrated scoring, accuracy study or real-outcome validation
  has been performed. The two live reports supplied inferred risks without source
  quotations; the interface correctly displays zero quotation matches. Matching a
  quotation only verifies its presence in the submitted text, not its truth.
- LLM latency and instruction following vary. A valid report may still contain
  weak or incorrect analysis. A token-capped, incomplete response is rejected
  rather than given a substitute score. Timeout is 180 seconds after connection.
- Browser checks used responsive Chromium. Physical iPhone/Safari and Android
  devices, other browser engines, screen readers and formal accessibility
  certification were not tested.
- This is a loopback-only, single-user portfolio application. It is not a shared
  production service. No authentication, tamper-proof audit, encryption-at-rest,
  multi-user authorisation or external approval enforcement is implemented.
- Reviewer names are locally entered. Test reviews are explicitly marked as QA
  and attached only to labelled sample reports.
- Source archives exclude virtual environments, SQLite/user data and downloaded
  models. Install dependencies and Ollama separately when moving to another PC.
- The GitHub repository and Astrix `public_html` website were not changed.

## Delivery

The source archive is checked for ZIP CRC integrity and each member is compared
against its source SHA-256. The adjacent delivery manifest records member hashes,
the archive hash and the verification result. Screenshots are saved outside the
application source folder.
