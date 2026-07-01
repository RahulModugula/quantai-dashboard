# Distressed-credit examples

Worked examples showing that the QuantAI 4-agent debate loop is not
equity-specific — swap the system prompts and the orchestrator becomes a
credit investment committee.

## Case Studies

### ATI Physical Therapy — April 2023 TSA

The flagship example. Analyzes the **April 11, 2023 Transaction Support
Agreement** at ATI Physical Therapy, where HPS Investment Partners (1L
lender representative) and a new-money participant group restructured the
cap stack via a $25M new-money + $100M 1L-to-2L-exchange second-lien PIK
convertible facility.

This is the actual entry point for a loan-to-own distressed trade — the
more-famous August 2025 take-private at $2.85/share / $523M TEV (~11.2x
LTM EBITDA, led by Knighthead Capital + Marathon Asset Management) is the
*outcome* of the 2023 decision, not a separate trade.

**Key Characteristics:**
- **Sector:** Outpatient physical therapy / healthcare services
- **Situation Type:** Out-of-court restructuring (Transaction Support Agreement)
- **Distress Driver:** Supply-side shock (PT wage inflation, therapist attrition)
- **Asset Type:** Asset-light (leased clinics, intangible relationships)
- **Resolution:** Take-private by Knighthead Capital + Marathon Asset Management (August 2025)
- **Time in Distress:** 28 months

Files:
- [`ati_2023.py`](ati_2023.py) — situation data + runner
- [`ati_2023_memo.md`](ati_2023_memo.md) — pre-rendered sample IC memo
- [`agents.py`](agents.py) — credit-focused agent subclasses (shared across examples)

### Run

```bash
# From repo root. Requires LLM API key (ANTHROPIC_API_KEY or OPENAI_API_KEY).
python -m examples.distressed.ati_2023
# Writes a freshly-generated memo to ati_2023_live_memo.md
```

### Envision Healthcare — May 2023 Chapter 11

**A second worked example, to show the same loop runs on a different situation.**
Analyzes the **May 2023 Chapter 11 filing** at Envision Healthcare, where KKR led
a pre-packaged restructuring with $2.6B of DIP financing and a debt-to-equity plan.

> **Note on sourcing.** Unlike the three bundled YAML situations (ATI, Serta,
> Hertz), the Envision figures are **approximate and illustrative** — assembled to
> demonstrate that the framework generalizes across sectors and structures, not
> line-by-line reconciled to Envision's filings. Treat its numbers as a
> structure/shape example, not a sourced model.

**Key Characteristics:**
- **Sector:** Emergency medical services / ambulance transportation
- **Situation Type:** Chapter 11 bankruptcy (pre-packaged)
- **Distress Driver:** Demand-side shock (CMS reimbursement pressure, state rate caps)
- **Asset Type:** Asset-heavy (ambulances, bases, equipment)
- **Resolution:** Take-private by KKR (April 2024)

Files:
- [`envision_2023.py`](envision_2023.py) — situation data + runner
- [`envision_2023_memo.md`](envision_2023_memo.md) — pre-rendered sample IC memo

### Run

```bash
# From repo root. Requires LLM API key (ANTHROPIC_API_KEY or OPENAI_API_KEY).
python -m examples.distressed.envision_2023
# Writes a freshly-generated memo to envision_2023_live_memo.md
```

## What the two examples show

The point of running the same loop on ATI (out-of-court TSA, asset-light,
supply-side) and Envision (Chapter 11, asset-heavy, demand-side) is that the
framework **generalizes** — the agents and deterministic tools adapt to different
sectors, structures, and restructuring types without code changes.

| Dimension | ATI Physical Therapy | Envision Healthcare |
|-----------|---------------------|---------------------|
| Sector | Outpatient PT | Emergency services |
| Situation type | Out-of-court TSA | Chapter 11 pre-packaged |
| Distress driver | Supply-side (labor) | Demand-side (reimbursement) |
| Asset type | Asset-light | Asset-heavy |
| Resolution | Take-private | Take-private |

**On outcomes:** for ATI, the later take-private (Aug 2025, $523.3M TEV, ~11.2x)
is consistent with the committee's base/bull thesis — shown as **directional
context, not a forecast the tool produced.** This is an analysis and education
tool; it makes no predictive-accuracy claim, and the ATI numbers are the sourced,
reconciled ones (see the [`ati_2023.yaml`](situations/ati_2023.yaml) reconciliation
comments). The Envision figures are illustrative (see the note above).

### Common distress indicators worth checking

Going-concern disclosure; Debt/EBITDA well above sustainable levels; interest
coverage below ~1.0x; covenant breaches; liquidity pressure (revolver draws, cash
burn). These are heuristics the agents surface, not a scoring model.

### How it differs from the equity agents

| Equity (`src/agents/`) | Credit (`examples/distressed/agents.py`) |
|------------------------|------------------------------------------|
| `QuantAgent` — ML signal + SHAP + technicals | `CapStructureAgent` — leverage, coverage, recovery per tranche |
| `NewsAgent` — yfinance + SEC EDGAR | `SituationAgent` — docket/timeline/catalyst analysis |
| `RiskAgent` — devil's advocate on next-day trade | `CreditRiskAgent` — devil's advocate on recovery math + process risk |
| `PortfolioManagerAgent` — BUY/SELL/HOLD | `CreditCommitteeAgent` — full IC memo with sizing, instrument, vote |

Same `BaseAgent` LiteLLM tool-call loop. Same orchestration phases. Different
prompts, different output format, different asset class.

### Data model

`examples/distressed/agents.py` defines two dataclasses:

- `CapitalStructureTranche` — one layer of the stack (face, coupon, maturity, seniority, price, holder)
- `Situation` — everything the committee needs (company, sector, timeline, cap stack, operating metrics, known risks)

Both render cleanly into the markdown prompts the agents read. Adding a new
case study is mechanical: instantiate a new `Situation`, call
`run_credit_committee`, write the result.

### Why this matters for the overall project

The equity pipeline is one instance of a more general pattern:

1. Structured input data (prices + ML features, or cap stack + docket)
2. Specialist agents with domain prompts and optional tools
3. Parallel phase → risk-challenger phase → committee-memo phase
4. Full audit trail in SQLite

The prompts and tool bindings change per asset class; the orchestration does
not. This is the asset-class-agnostic architecture summary in a single
directory.
