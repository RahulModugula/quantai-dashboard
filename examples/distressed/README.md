# Distressed-credit examples

Worked examples showing that the QuantAI 4-agent debate loop is not
equity-specific — swap the system prompts and the orchestrator becomes a
credit investment committee.

## ATI Physical Therapy — April 2023 TSA

The flagship example. Analyzes the **April 11, 2023 Transaction Support
Agreement** at ATI Physical Therapy, where HPS Investment Partners (1L
lender representative) and a new-money participant group restructured the
cap stack via a $25M new-money + $100M 1L-to-2L-exchange second-lien PIK
convertible facility.

This is the actual entry point for a loan-to-own distressed trade — the
more-famous August 2025 take-private at $2.85/share / $523M TEV (~11.2x
LTM EBITDA, led by Knighthead Capital + Marathon Asset Management) is the
*outcome* of the 2023 decision, not a separate trade.

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
