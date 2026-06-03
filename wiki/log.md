# Wiki Log

## 2026-06-03 ingest | Initial build

- Source: `D:\My Projects\BSA` (BSA Engine — Bank Statement Analyzer)
- Files read: 49 source files (backend Python + frontend React/CSS); all read in full
- Pages written: 37 (+ _overview, index, log) · graph.html = 37 nodes, 195 edges
- Layers identified: API/UI, Domain (pipeline + detectors), Infra (parsers), Config, Utils, UI Components
- God nodes: [[compute_analysis]], [[FastAPIApp]], [[Lexicon]], [[helpers]], [[Settings]], [[ResultsPage]]
- Notes:
  - No automated tests in the repo; output is not validated against [[AnalysisResponse]] at runtime.
  - Behavioural [[Lexicon]] categories are ported but not yet fired.
  - `GAMBLING_KEYWORDS`/`CRYPTO_KEYWORDS` in [[Settings]] are now dead (superseded by [[Lexicon]]).
  - Presentational charts/table merged into a single [[VizComponents]] page.
  - All connections were read directly from source (no inferred dependencies).
