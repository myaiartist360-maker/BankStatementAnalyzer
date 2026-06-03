"""Generate graph.html from the wiki pages' [[wikilinks]]. Run once; no deps."""
import json, re, pathlib

WIKI = pathlib.Path(__file__).parent
PAGES = WIKI / "pages"
OUT = WIKI.parent / "graph.html"

# node -> (layer, type, file, summary)
META = {
    "FastAPIApp": ("api", "module", "backend/main.py", "HTTP entry point + four-stage pipeline orchestrator."),
    "AnalysisRequest": ("api", "module", "backend/models/request_models.py", "Pydantic input contracts for analyse + feedback."),
    "AnalysisResponse": ("api", "module", "backend/models/response_models.py", "Full output contract for the engine."),
    "App": ("ui", "module", "frontend/src/App.jsx", "React shell + router."),
    "UploadPage": ("ui", "component", "frontend/src/pages/UploadPage.jsx", "Upload + analyse screen."),
    "ResultsPage": ("ui", "component", "frontend/src/pages/ResultsPage.jsx", "Tabbed analysis dashboard (frontend hub)."),
    "DrillDownModal": ("ui", "component", "frontend/src/components/DrillDownModal.jsx", "Generic provenance modal: formula + source rows."),
    "IncomeAnalysis": ("ui", "component", "frontend/src/components/IncomeAnalysis.jsx", "Income tab."),
    "ExpenseAnalysis": ("ui", "component", "frontend/src/components/ExpenseAnalysis.jsx", "Expenses tab."),
    "CreditAssessment": ("ui", "component", "frontend/src/components/CreditAssessment.jsx", "Credit tab."),
    "RiskFlags": ("ui", "component", "frontend/src/components/RiskFlags.jsx", "Risk tab."),
    "TamperReport": ("ui", "component", "frontend/src/components/TamperReport.jsx", "Tamper tab."),
    "FeedbackPanel": ("ui", "component", "frontend/src/components/FeedbackPanel.jsx", "Feedback tab."),
    "VizComponents": ("ui", "component", "frontend/src/components/*.jsx", "Charts + transaction table."),
    "ingest": ("domain", "function", "backend/pipeline/ingestion.py", "Step 1: detect, decrypt, parse, route."),
    "run_tamper_checks": ("domain", "function", "backend/pipeline/tamper.py", "Step 2: eight integrity checks."),
    "enrich_transactions": ("domain", "module", "backend/pipeline/extraction.py", "Step 3: derive mode/reversal, filter."),
    "ensure_chronological": ("domain", "function", "backend/pipeline/extraction.py", "Reorder newest-first statements."),
    "compute_analysis": ("domain", "function", "backend/pipeline/analysis.py", "Step 4: all financial metrics (analytical hub)."),
    "income_detector": ("domain", "module", "backend/detectors/income_detector.py", "Categorised income + payers."),
    "expense_detector": ("domain", "module", "backend/detectors/expense_detector.py", "Categorised obligations/spend + FOIR inputs."),
    "salary_detector": ("domain", "module", "backend/detectors/salary_detector.py", "Recurring salary detection."),
    "emi_detector": ("domain", "module", "backend/detectors/emi_detector.py", "EMI clusters + bounces."),
    "gambling_detector": ("domain", "module", "backend/detectors/gambling_detector.py", "Gaming/betting spend."),
    "crypto_detector": ("domain", "module", "backend/detectors/crypto_detector.py", "Crypto/VDA flows."),
    "roundtrip_detector": ("domain", "module", "backend/detectors/roundtrip_detector.py", "Fund-cycling pairs."),
    "credit_score": ("domain", "module", "backend/detectors/credit_score.py", "Composite credit assessment."),
    "parse_digital_pdf": ("infra", "function", "backend/parsers/pdf_parser.py", "Text-layer PDF parser."),
    "parse_scanned_pdf": ("infra", "function", "backend/parsers/ocr_parser.py", "OCR parser + pixel anomalies."),
    "parse_aa_json": ("infra", "function", "backend/parsers/aa_parser.py", "RBI Account Aggregator JSON parser."),
    "zip_handler": ("infra", "module", "backend/parsers/zip_handler.py", "Multi-file ZIP merge."),
    "Settings": ("config", "config", "backend/config.py", "Thresholds, flags, legacy patterns."),
    "Lexicon": ("config", "module", "backend/lexicon.py", "Master narration vocabulary (53 categories)."),
    "helpers": ("utils", "module", "backend/utils/helpers.py", "Dates/amounts/hashing (shared foundation)."),
    "balance_checker": ("utils", "module", "backend/utils/balance_checker.py", "Running-balance continuity."),
    "password_cracker": ("utils", "module", "backend/utils/password_cracker.py", "Indian-bank PDF password patterns."),
    "Improvements": ("other", "concept", "IMPROVEMENTS.md", "Known gaps / backlog."),
}

# Collect directed edges from wikilinks (dedup).
edges = set()
link_re = re.compile(r"\[\[([^\]]+)\]\]")
for f in PAGES.glob("*.md"):
    src = f.stem
    for m in link_re.findall(f.read_text(encoding="utf-8")):
        tgt = m.strip()
        if tgt in META and tgt != src:
            edges.add((src, tgt))

# Inbound degree = how many pages link TO a node.
indeg = {n: 0 for n in META}
for s, t in edges:
    indeg[t] += 1

nodes = [{
    "id": n, "label": n, "layer": META[n][0], "type": META[n][1],
    "file": META[n][2], "summary": META[n][3], "degree": indeg[n],
} for n in META]
edge_list = [{"from": s, "to": t} for s, t in sorted(edges)]

TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>BSA Engine — Codebase Graph</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css"/>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#0d1117;font-family:'Segoe UI',monospace}
  #graph{width:100vw;height:100vh}
  #panel{position:fixed;top:12px;left:12px;background:#161b22;color:#c9d1d9;
         padding:14px 16px;border-radius:8px;border:1px solid #30363d;
         font-size:13px;max-width:300px;z-index:10}
  #panel h2{color:#58a6ff;font-size:15px;margin-bottom:8px}
  #detail{margin-top:10px;border-top:1px solid #30363d;padding-top:10px;
          font-size:12px;color:#8b949e;min-height:40px}
  #search{position:fixed;top:12px;right:12px;background:#161b22;
          border:1px solid #30363d;color:#c9d1d9;padding:8px 12px;
          border-radius:6px;font-size:13px;width:200px;z-index:10}
  #search:focus{outline:none;border-color:#58a6ff}
  #legend{position:fixed;bottom:16px;left:12px;background:#161b22;
          border:1px solid #30363d;border-radius:8px;padding:12px;
          font-size:11px;color:#8b949e;z-index:10}
  .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
</style>
</head>
<body>
<div id="panel">
  <h2>🏦 BSA Engine — Wiki Graph</h2>
  <div id="stats"></div>
  <div id="detail">Click a node to inspect. Larger nodes = more inbound links.</div>
</div>
<input id="search" placeholder="Search nodes…" oninput="doSearch(this.value)"/>
<div id="graph"></div>
<div id="legend"></div>
<script>
const COLORS={api:'#4E79A7',ui:'#B07AA1',auth:'#E15759',domain:'#59A14F',
              utils:'#F28E2B',config:'#EDC948',infra:'#76B7B2',other:'#BAB0AC'};
const LAYER_LABEL={api:'API / contracts',ui:'Frontend UI',domain:'Domain (pipeline+detectors)',
              utils:'Utils',config:'Config',infra:'Parsers / infra',other:'Meta'};
const RAW_NODES=__NODES__;
const RAW_EDGES=__EDGES__;
const layers=[...new Set(RAW_NODES.map(n=>n.layer||'other'))];
document.getElementById('legend').innerHTML=
  layers.map(l=>`<div style="margin:3px 0"><span class="dot" style="background:${COLORS[l]||COLORS.other}"></span>${LAYER_LABEL[l]||l}</div>`).join('');
document.getElementById('stats').innerHTML=`${RAW_NODES.length} nodes · ${RAW_EDGES.length} edges`;
const nodes=new vis.DataSet(RAW_NODES.map(n=>({
  id:n.id,label:n.label,
  title:`${n.label} — ${n.type}\n${n.file}\n${n.summary}`,
  color:{background:COLORS[n.layer]||COLORS.other,border:'#1a1a2e',
         highlight:{background:'#FFD700',border:'#1a1a2e'}},
  size:Math.max(10,(n.degree||1)*6),
  font:{color:'#fff',size:n.degree>3?15:12},
  borderWidth:n.degree>4?3:1,
})));
const edges=new vis.DataSet(RAW_EDGES.map((e,i)=>({
  id:i,from:e.from,to:e.to,arrows:'to',
  color:{color:'#3a3a4a',opacity:0.7},
  smooth:{type:'continuous',roundness:0.3},
})));
const net=new vis.Network(document.getElementById('graph'),{nodes,edges},
  {physics:{solver:'forceAtlas2Based',
    forceAtlas2Based:{gravitationalConstant:-58,springLength:140,damping:0.5},
    stabilization:{iterations:300}},
   interaction:{hover:true,keyboard:true,tooltipDelay:120}});
net.on('click',p=>{
  if(!p.nodes.length)return;
  const n=RAW_NODES.find(x=>x.id===p.nodes[0]);
  document.getElementById('detail').innerHTML=
    `<b style="color:#c9d1d9">${n.label}</b> `+
    `<span style="color:${COLORS[n.layer]}">●</span> ${n.type}<br>`+
    `<span style="color:#8b949e">${n.file}</span><br>`+
    `<span style="color:#6e7681">${n.degree} inbound link(s)</span><br><br>${n.summary}`;
});
function doSearch(q){
  if(!q){nodes.update(RAW_NODES.map(n=>({id:n.id,hidden:false})));return;}
  nodes.update(RAW_NODES.map(n=>({id:n.id,hidden:!n.label.toLowerCase().includes(q.toLowerCase())})));
}
</script>
</body>
</html>"""

html = TEMPLATE.replace("__NODES__", json.dumps(nodes)).replace("__EDGES__", json.dumps(edge_list))
OUT.write_text(html, encoding="utf-8")
print(f"Wrote {OUT} | {len(nodes)} nodes, {len(edge_list)} edges")
top = sorted(nodes, key=lambda n: n["degree"], reverse=True)[:6]
print("Top by inbound degree:", ", ".join(f'{n["label"]}({n["degree"]})' for n in top))
