# Changelog

All notable changes to this project are documented here. The format loosely
follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added — the credit committee becomes a tool

- **`quantai-credit` CLI** — run the AI distressed-credit committee on any
  situation described in a YAML/JSON file (`run`), scaffold a template (`new`),
  list bundled examples (`list`).
- **`quantai-credit validate`** — a free, no-LLM pre-flight that computes a
  cap-structure snapshot (leverage, coverage, attachment/detachment in turns of
  EBITDA, maturity wall) and flags data-completeness issues before you pay for a
  run. Emits `--json` for pipelines.
- **Machine-readable output** — `run` writes both a human memo (`<deal>_memo.md`)
  and a structured result (`<deal>.json`: parsed recommendation/sizing/target/
  catalyst/vote + the computed snapshot + token usage).
- **Deeper deterministic credit tools** — pari-passu pro-rata recovery
  waterfall, super-priority/admin claims paid off the top, configurable PIK
  accrual, attachment/detachment points, breakeven enterprise value per tranche,
  current yield / approximate YTM, and a maturity-wall summary. All unit-tested.
- **Three bundled, sourced example situations** — ATI Physical Therapy (2023 TSA,
  PIK-convertible fulcrum), Serta Simmons (2020 uptier / liability management),
  and Hertz (2020 Chapter 11, asset-coverage / fleet-ABS). Figures grounded in
  public filings with approximations marked inline.
- **Lightweight install path** — the credit committee now runs on `litellm` +
  `pyyaml` + `rich` alone (`requirements-credit.txt`); the heavy ML/dashboard
  stack is no longer pulled in for credit-only use.
- **Rendered terminal SVGs** in the README (committee run + free validate
  snapshot), regenerable via `scripts/render_demo_svg.py`.

### Changed

- Repositioned the project around the distressed-credit committee; the equity
  ML pipeline is now framed as a second proof of the shared agent architecture.
- `src/agents` lazily imports the equity orchestrator (PEP 562) so importing the
  credit committee no longer drags in torch/pandas/etc.
- Example seniority ranks corrected for the pari-passu waterfall (ATI 1L senior
  to the 2L PIK; Serta uptier modeled as a strict priming order; Hertz fleet-ABS
  moved out of the corporate waterfall as a separate non-recourse silo).

### Fixed

- Live-feed tests no longer break under newer `pytest-asyncio` (switched from
  the deprecated `get_event_loop().run_until_complete()` to `asyncio.run()`).
- Pinned dev test tooling with upper bounds and pinned the asyncio fixture loop
  scope, so CI can't silently break on a new major release. CI now also lints
  `examples/` and `scripts/`.
