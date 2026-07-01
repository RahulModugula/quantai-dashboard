# Changelog

All notable changes to this project are documented here. The format loosely
follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed — credit-first packaging and honest math

- **Package renamed to `quantai-credit`** with a credit-first description. The
  default `pip install -e .` now installs the committee on **three deps**
  (`litellm`, `pyyaml`, `rich`) with **no ML stack**. The equity pipeline / API /
  dashboard moved behind an optional `equity` extra (`pip install -e ".[equity]"`).
  A dedicated CI job proves the lightweight install runs `validate` with no key.
- **Corrected the bundled examples' debt totals (removed double-counts).**
  - ATI: the 1L is carried at its **$400M post-exchange** balance (was $500M while
    also counting the $100M exchanged into the new 2L PIK), and the $165M Series A
    Preferred is treated as equity-like and **excluded from Debt/EBITDA**. The
    snapshot now ties to **$575M / 85.8x** (was a contradictory $840M / 125.4x).
  - Serta: the $850M FLSO "roll-up" is repositioned old debt, so the old 1L/2L are
    carried at **non-participating residuals**, not full face — pro-forma debt is
    **$2.76B / 10.6x** (was ~$3.6B). Added a derived LTM EBITDA that reconciles
    Moody's leverage points.
- **Removed the internal "validation" write-ups** (methodology / summary /
  production-readiness / comparative) that overstated "predictive validity" and
  admitted unverified figures. Outcomes are now framed as directional context, not
  forecasts; the Envision case is labeled illustrative, not filing-sourced.

### Fixed — credit math correctness

- **Fulcrum at an exact claim boundary** — the fulcrum is now the most-senior
  *impaired* claim (previously a strict `0 < r < 100` test silently missed the
  boundary case).
- **Tool consistency** — face value is the single canonical claim across the
  waterfall, breakeven, and attach/detach; PIK accrual is opt-in (off by default)
  and applied identically everywhere, so the tools no longer disagree.
- **Preferred/equity is no longer counted as funded debt** in leverage/total-debt.
- **Structural guardrails** — `validate` warns loudly on non-pro-rata uptiers and
  asset-backed / bankruptcy-remote silos, which the generic pari-passu waterfall
  cannot model, and ships an `asset_coverage_ratio` / `collateral_recovery_pct`
  primitive for the silo case.
- Regression tests added for each of the above (`tests/test_credit_correctness.py`).

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
- **Lightweight install path** — the credit committee runs on `litellm` +
  `pyyaml` + `rich` alone (the default `pip install`); the heavy ML/dashboard
  stack is behind the `equity` extra and no longer pulled in for credit-only use.
- **Rendered terminal SVGs** in the README (committee run + free validate
  snapshot), regenerable via `scripts/render_demo_svg.py`.

### Changed

- Repositioned the project around the distressed-credit committee; the equity
  ML pipeline is now framed as a second proof of the shared agent architecture.
- `src/agents` lazily imports the equity orchestrator (PEP 562) so importing the
  credit committee no longer drags in torch/pandas/etc.
- Example seniority ranks set for the pari-passu waterfall (ATI 1L senior to the
  2L PIK; Serta uptier modeled as a priming order with a loud caveat that the
  generic waterfall does not adjudicate the priming dispute; Hertz fleet-ABS kept
  out of the corporate waterfall as a separate non-recourse silo).

### Fixed

- Live-feed tests no longer break under newer `pytest-asyncio` (switched from
  the deprecated `get_event_loop().run_until_complete()` to `asyncio.run()`).
- Pinned dev test tooling with upper bounds and pinned the asyncio fixture loop
  scope, so CI can't silently break on a new major release. CI now also lints
  `examples/` and `scripts/`.
