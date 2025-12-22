from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime
from agent import assess_decision

app = FastAPI()

HISTORY = []  # last runs

class AssessIn(BaseModel):
    decision: str

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>AegisAI – Decision Guardrail Agent</title>
  <style>
    :root{
      --bg:#060913;
      --panel:rgba(255,255,255,.06);
      --panel2:rgba(255,255,255,.04);
      --border:rgba(255,255,255,.12);
      --text:#e9eefc;
      --muted:rgba(233,238,252,.68);
      --ok:#2ee59d;
      --warn:#ffcc66;
      --bad:#ff6b6b;
      --cyan:#7bd0ff;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      background:
        radial-gradient(900px 500px at 15% 15%, rgba(123,208,255,.12), transparent 60%),
        radial-gradient(900px 500px at 80% 20%, rgba(255,204,102,.10), transparent 55%),
        linear-gradient(180deg, #040610, var(--bg));
      color:var(--text);
      min-height:100vh;
    }
    .wrap{max-width:1350px;margin:0 auto;padding:18px 18px 28px}
    .top{
      display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;
      padding:16px;border-radius:18px;
      background:linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.05));
      border:1px solid var(--border);
      box-shadow:0 12px 50px rgba(0,0,0,.35);
    }
    .brand{display:flex;align-items:center;gap:12px}
    .mark{
      width:12px;height:12px;border-radius:4px;
      background:linear-gradient(135deg, var(--cyan), var(--ok));
      box-shadow:0 0 20px rgba(123,208,255,.35);
      transform:rotate(12deg);
    }
    .title{font-weight:1000;font-size:18px;letter-spacing:.2px}
    .sub{margin-top:2px;color:var(--muted);font-size:13px}
    .metaRow{display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end;align-items:center}
    .pill{
      padding:8px 10px;border-radius:999px;border:1px solid var(--border);
      background:rgba(255,255,255,.05);font-size:12px;color:var(--muted)
    }
    .pill b{color:var(--text)}
    .grid{
      margin-top:14px;
      display:grid;
      grid-template-columns: 1.05fr .95fr;
      gap:14px;
      align-items:stretch;
    }
    @media(max-width:1100px){ .grid{grid-template-columns:1fr} }
    .card{
      border-radius:18px;
      background:linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.04));
      border:1px solid var(--border);
      box-shadow:0 10px 35px rgba(0,0,0,.28);
      overflow:hidden;
    }
    .head{
      padding:14px 14px 10px;
      display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;
      border-bottom:1px solid rgba(255,255,255,.08);
    }
    h3{margin:0;font-size:15px}
    .hint{margin-top:4px;color:var(--muted);font-size:12px}
    .body{padding:14px}
    textarea{
      width:100%;
      min-height:360px;
      border-radius:18px;
      border:1px solid rgba(255,255,255,.12);
      background:rgba(0,0,0,.20);
      color:var(--text);
      padding:14px;
      outline:none;
      resize:vertical;
      font-size:13.5px;
      line-height:1.45;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }
    .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
    select, button{
      height:42px;border-radius:14px;border:1px solid var(--border);
      background:rgba(255,255,255,.07);color:var(--text);padding:0 12px;outline:none;
      font-weight:800;cursor:pointer;
    }
    button:hover{background:rgba(255,255,255,.11)}
    .btnPrimary{background:rgba(123,208,255,.12); border-color: rgba(123,208,255,.25)}
    .btnPrimary:hover{background:rgba(123,208,255,.16)}
    .btnGhost{background:rgba(255,255,255,.05); font-weight:700}

    /* CONTROL-ROOM PANELS */
    .rightGrid{
      display:grid;
      grid-template-columns: 1fr 1fr;
      gap:12px;
    }
    @media(max-width:1100px){ .rightGrid{grid-template-columns:1fr} }

    .panel{
      padding:12px;
      border-radius:16px;
      background:rgba(255,255,255,.04);
      border:1px solid rgba(255,255,255,.08);
    }
    .label{color:var(--muted);font-size:12px}
    .big{font-weight:1000;font-size:22px;margin-top:6px}
    .riskBar{
      margin-top:10px;
      height:12px;border-radius:999px;
      background:rgba(255,255,255,.06);
      border:1px solid rgba(255,255,255,.10);
      overflow:hidden;
    }
    .riskFill{height:100%;width:0%}
    .divider{height:1px;background:rgba(255,255,255,.08);margin:10px 0}
    .kv{display:flex;justify-content:space-between;gap:10px;margin-top:6px}
    .kv span{color:var(--muted);font-size:12px}
    .kv b{font-size:12px}

    .terminal{
      border-radius:18px;
      border:1px solid rgba(255,255,255,.12);
      background:rgba(0,0,0,.22);
      padding:14px;
      white-space:pre-wrap;
      line-height:1.45;
      font-size:13.5px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      min-height:240px;
      overflow:auto;
    }
    .chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
    .chip{
      border-radius:999px;
      padding:7px 10px;
      border:1px solid rgba(255,255,255,.10);
      background:rgba(255,255,255,.05);
      color:var(--muted);
      font-size:12px;
    }
    .timeline{display:flex;flex-direction:column;gap:10px;max-height:260px;overflow:auto;padding-right:4px}
    .tItem{
      padding:10px 12px;border-radius:16px;
      background:rgba(255,255,255,.04);
      border:1px solid rgba(255,255,255,.08);
    }
    .tTop{display:flex;justify-content:space-between;gap:10px;align-items:center}
    .tag{
      font-size:12px;
      padding:4px 8px;border-radius:999px;
      border:1px solid rgba(255,255,255,.10);
      background:rgba(255,255,255,.05);
      color:var(--muted);
    }
    .when{color:var(--muted);font-size:12px}
    .footer{margin-top:12px;color:var(--muted);font-size:12px;text-align:center;opacity:.95}
  </style>
</head>
<body>
<div class="wrap">

  <div class="top">
    <div class="brand">
      <div class="mark"></div>
      <div>
        <div class="title">AegisAI – Decision Guardrail Agent</div>
        <div class="sub">Pre-mortem risk analysis • Approve / Revise / Block • Control-room interface</div>
      </div>
    </div>
    <div class="metaRow">
      <div class="pill">Status: <b id="status">Idle</b></div>
      <div class="pill">Last run: <b id="stamp">—</b></div>
      <div class="pill">Engine: <b>Ollama (LLaMA 3)</b></div>
    </div>
  </div>

  <div class="grid">

    <!-- LEFT INPUT -->
    <div class="card">
      <div class="head">
        <div>
          <h3>Decision Proposal</h3>
          <div class="hint">Paste a decision, constraints, and context. AegisAI predicts risks and recommends guardrails.</div>
        </div>
        <div class="row">
          <select id="preset">
            <option value="0">Preset 1 — Cloud Cost Cut</option>
            <option value="1">Preset 2 — Product Launch Rush</option>
            <option value="2">Preset 3 — Layoff + Delivery</option>
            <option value="3">Preset 4 — Compliance Deadline</option>
          </select>
          <button class="btnGhost" id="load">Load</button>
          <button class="btnGhost" id="clear">Clear</button>
          <button class="btnPrimary" id="run">Assess Risk</button>
        </div>
      </div>
      <div class="body">
        <textarea id="decision" placeholder="Example: We will cut cloud spend by 30% in 60 days by migrating…"></textarea>
        <div class="chips" id="chips"></div>
      </div>
    </div>

    <!-- RIGHT OUTPUT (CONTROL ROOM) -->
    <div class="card">
      <div class="head">
        <div>
          <h3>Risk Control Panel</h3>
          <div class="hint">Executive-ready risk rating with guardrails + monitoring signals.</div>
        </div>
        <div class="row">
          <button class="btnGhost" id="copy">Copy Report</button>
        </div>
      </div>
      <div class="body">

        <div class="rightGrid">
          <div class="panel">
            <div class="label">Overall Risk Level</div>
            <div class="big" id="riskLevel">—</div>
            <div class="riskBar"><div class="riskFill" id="riskFill"></div></div>
            <div class="kv"><span>Risk score</span><b id="riskScore">—</b></div>
            <div class="kv"><span>Confidence</span><b id="confidence">—</b></div>
          </div>

          <div class="panel">
            <div class="label">Decision Recommendation</div>
            <div class="big" id="recommend">—</div>
            <div class="divider"></div>
            <div class="label">Action Buttons (demo)</div>
            <div class="row" style="margin-top:10px">
              <button class="btnGhost" id="btnApprove">APPROVE</button>
              <button class="btnGhost" id="btnRevise">REVISE</button>
              <button class="btnGhost" id="btnBlock">BLOCK</button>
            </div>
            <div class="hint" style="margin-top:8px">These simulate a decision workflow; recommendation is generated by the agent.</div>
          </div>
        </div>

        <div style="margin-top:12px" class="panel">
          <div class="label">Executive Brief</div>
          <div class="terminal" id="exec">Run an assessment to generate a report.</div>
        </div>

        <div style="margin-top:12px" class="rightGrid">
          <div class="panel">
            <div class="label">Guardrails</div>
            <div class="terminal" id="guards" style="min-height:200px"></div>
          </div>
          <div class="panel">
            <div class="label">Monitoring Signals</div>
            <div class="terminal" id="signals" style="min-height:200px"></div>
          </div>
        </div>

        <div style="margin-top:12px">
          <h3 style="margin:0 0 8px 0;font-size:14px">Run Timeline</h3>
          <div class="timeline" id="timeline"></div>
        </div>

      </div>
    </div>

  </div>

  <div class="footer">
    Interview line: “SentinelAI explains what changed. AegisAI protects decisions by predicting what could go wrong next.”
  </div>

</div>

<script>
const $ = (id)=>document.getElementById(id);

const PRESETS = [
`PROPOSED DECISION:
- Reduce cloud costs by 30% within 60 days by migrating services to a cheaper provider.
- Increase deployment frequency to weekly to maintain feature delivery during migration.

CONSTRAINTS:
- No additional headcount.
- SLA penalties apply for downtime.
- Customer support backlog has increased slightly.

TASK:
Assess operational, financial, and reputational risk and recommend guardrails for the next 30 days.`,
`PROPOSED DECISION:
- Launch a new consumer product in 3 weeks to meet a marketing deadline.
- Freeze QA scope to only smoke tests due to time constraints.
- Increase ad spend by 40% at launch.

CONSTRAINTS:
- Returns policy is strict.
- Brand reputation depends on product reliability.

TASK:
Assess risks, identify second-order impacts, and propose guardrails and monitoring signals.`,
`PROPOSED DECISION:
- Reduce engineering headcount by 15% immediately.
- Maintain same delivery targets for Q1.
- Rotate on-call across fewer staff to keep 24/7 coverage.

CONSTRAINTS:
- Core services are legacy and have limited test coverage.
- Two senior engineers are leaving next month.

TASK:
Assess delivery and reliability risks and recommend mitigation steps.`,
`PROPOSED DECISION:
- Implement new compliance requirements within 4 weeks.
- Update data retention and access controls.
- Keep current release schedule unchanged.

CONSTRAINTS:
- Penalties apply for non-compliance.
- Multiple teams depend on shared data pipelines.

TASK:
Assess compliance, operational, and delivery risk; recommend guardrails and monitoring signals.`
];

function setStatus(t){ $("status").textContent = t; }
function setStamp(t){ $("stamp").textContent = t; }

function riskColor(level){
  const L = (level||"").toUpperCase();
  if(L === "LOW") return "var(--ok)";
  if(L === "MEDIUM") return "var(--warn)";
  if(L === "HIGH" || L === "CRITICAL") return "var(--bad)";
  return "rgba(255,255,255,.35)";
}

function renderTimeline(items){
  const root = $("timeline");
  root.innerHTML = "";
  if(!items || !items.length){
    root.innerHTML = '<div class="tItem"><div class="tTop"><span class="tag">No runs yet</span><span class="when">—</span></div></div>';
    return;
  }
  for(const it of items.slice(0,6)){
    const div = document.createElement("div");
    div.className = "tItem";
    div.innerHTML = `
      <div class="tTop">
        <span class="tag">${it.reco} • ${it.level} • ${it.score}</span>
        <span class="when">${it.when}</span>
      </div>
      <div class="when" style="margin-top:6px">${it.note}</div>
    `;
    root.appendChild(div);
  }
}

function bullets(arr){
  if(!arr || !arr.length) return "";
  return arr.map(x => "• " + x).join("\\n");
}

function tagChips(text){
  const s = text.toLowerCase();
  const tags = [];
  if(s.includes("cloud") || s.includes("migration")) tags.push("Cloud/Migration");
  if(s.includes("compliance") || s.includes("retention")) tags.push("Compliance");
  if(s.includes("launch") || s.includes("marketing")) tags.push("Launch");
  if(s.includes("headcount") || s.includes("layoff")) tags.push("Capacity Risk");
  if(s.includes("sla") || s.includes("downtime")) tags.push("Reliability");
  if(s.includes("qa") || s.includes("test")) tags.push("Quality");
  return tags.slice(0,6);
}

function renderChips(tags){
  const root = $("chips");
  root.innerHTML = "";
  if(!tags.length) return;
  for(const t of tags){
    const div = document.createElement("div");
    div.className = "chip";
    div.textContent = t;
    root.appendChild(div);
  }
}

$("load").onclick = () => {
  const i = parseInt($("preset").value, 10);
  $("decision").value = PRESETS[i];
  renderChips(tagChips($("decision").value));
};

$("clear").onclick = () => {
  $("decision").value = "";
  renderChips([]);
};

$("decision").addEventListener("input", ()=>renderChips(tagChips($("decision").value)));

$("copy").onclick = async () => {
  const text =
`AegisAI Report
Risk Level: ${$("riskLevel").textContent}
Risk Score: ${$("riskScore").textContent}
Confidence: ${$("confidence").textContent}
Recommendation: ${$("recommend").textContent}

Executive Summary:
${$("exec").textContent}

Guardrails:
${$("guards").textContent}

Monitoring Signals:
${$("signals").textContent}`;
  try{
    await navigator.clipboard.writeText(text);
    setStatus("Copied");
    setTimeout(()=>setStatus("Idle"), 900);
  }catch(e){
    alert("Copy failed (browser permission).");
  }
};

function setDecisionButtons(reco){
  const a = $("btnApprove"), r = $("btnRevise"), b = $("btnBlock");
  [a,r,b].forEach(x=>x.style.borderColor="rgba(255,255,255,.12)");
  if(reco === "APPROVE") a.style.borderColor="var(--ok)";
  if(reco === "REVISE") r.style.borderColor="var(--warn)";
  if(reco === "BLOCK") b.style.borderColor="var(--bad)";
}

async function assess(){
  const txt = $("decision").value.trim();
  if(!txt){
    $("exec").textContent = "Paste a decision proposal or load a preset first.";
    return;
  }
  setStatus("Thinking…");
  $("exec").textContent = "Assessing risk…";

  const res = await fetch("/api/assess", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({decision: txt})
  });

  const data = await res.json();
  if(!res.ok || data.error){
    setStatus("Error");
    $("exec").textContent = "Error: " + (data.error || "Request failed");
    return;
  }

  $("riskLevel").textContent = data.overall_risk_level || "—";
  $("riskScore").textContent = (data.risk_score ?? "—") + " / 100";
  $("confidence").textContent = (data.confidence ?? "—");

  const reco = (data.decision_recommendation || "—").toUpperCase();
  $("recommend").textContent = reco;

  const c = riskColor(data.overall_risk_level);
  $("riskFill").style.background = c;
  $("riskFill").style.width = Math.max(0, Math.min(100, data.risk_score || 0)) + "%";

  setDecisionButtons(reco);

  $("exec").textContent =
`${data.executive_summary || ""}

PRIMARY RISKS:
${(data.primary_risks || []).map(r => `• ${r.title} [${r.severity}] — ${r.why}`).join("\\n")}

SECOND-ORDER EFFECTS:
${bullets(data.second_order_effects || [])}

30-DAY OUTLOOK:
• Best-case: ${data["30_day_outlook"]?.best_case || ""}
• Base-case: ${data["30_day_outlook"]?.base_case || ""}
• Worst-case: ${data["30_day_outlook"]?.worst_case || ""}`.trim();

  $("guards").textContent = bullets(data.guardrails || []);
  $("signals").textContent = bullets(data.monitoring_signals || []);

  setStamp(data.last_updated || "—");
  renderTimeline(data.history || []);

  setStatus("Done");
  setTimeout(()=>setStatus("Idle"), 1100);
}

$("run").onclick = assess;

// demo buttons (UI only)
$("btnApprove").onclick = ()=>alert("Demo: Decision marked APPROVE (workflow simulation).");
$("btnRevise").onclick = ()=>alert("Demo: Decision marked REVISE (workflow simulation).");
$("btnBlock").onclick = ()=>alert("Demo: Decision marked BLOCK (workflow simulation).");

// default load preset
$("preset").value = "0";
$("decision").value = PRESETS[0];
renderChips(tagChips($("decision").value));
renderTimeline([]);
</script>
</body>
</html>
"""

@app.post("/api/assess")
def api_assess(payload: AssessIn):
    try:
        result = assess_decision(payload.decision)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # history note (first line)
        first_line = payload.decision.strip().splitlines()[0] if payload.decision.strip() else "—"
        note = (first_line[:90] + "…") if len(first_line) > 90 else first_line

        HISTORY.insert(0, {
            "when": ts,
            "level": result.get("overall_risk_level", "—"),
            "score": f"{result.get('risk_score', '—')}/100",
            "reco": result.get("decision_recommendation", "—"),
            "note": note
        })
        del HISTORY[10:]

        result["last_updated"] = ts
        result["history"] = HISTORY
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
