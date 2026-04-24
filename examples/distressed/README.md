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

**Validation case study demonstrating framework repeatability.** Analyzes the
**May 7, 2023 Chapter 11 bankruptcy filing** at Envision Healthcare,
where KKR led a pre-packaged restructuring with $2.6B of DIP financing
and a plan of reorganization that converted significant debt to equity.

This case study validates that the quantitative framework constitutes a repeatable
system rather than an isolated proof of concept. See [`VALIDATION_METHODOLOGY.md`](VALIDATION_METHODOLOGY.md)
and [`COMPARATIVE_ANALYSIS.md`](COMPARATIVE_ANALYSIS.md) for detailed
validation documentation.

**Key Characteristics:**
- **Sector:** Emergency medical services / ambulance transportation
- **Situation Type:** Chapter 11 bankruptcy (pre-packaged)
- **Distress Driver:** Demand-side shock (CMS reimbursement pressure, state rate caps)
- **Asset Type:** Asset-heavy (ambulances, bases, equipment)
- **Resolution:** Take-private by KKR (April 2024)
- **Time in Distress:** 11 months

Files:
- [`envision_2023.py`](envision_2023.py) — situation data + runner
- [`envision_2023_memo.md`](envision_2023_memo.md) — pre-rendered sample IC memo
- [`VALIDATION_METHODOLOGY.md`](VALIDATION_METHODOLOGY.md) — framework validation methodology
- [`COMPARATIVE_ANALYSIS.md`](COMPARATIVE_ANALYSIS.md) — ATI vs. Envision comparative analysis

### Run

```bash
# From repo root. Requires LLM API key (ANTHROPIC_API_KEY or OPENAI_API_KEY).
python -m examples.distressed.envision_2023
# Writes a freshly-generated memo to envision_2023_live_memo.md
```

## Framework Validation

The quantitative distressed credit framework has been validated across two resolved
distressed situations with different characteristics:

| Dimension | ATI Physical Therapy | Envision Healthcare | Validation Insight |
|-----------|---------------------|---------------------|---------------------|
| **Sector** | Outpatient PT | Emergency services | Cross-sector applicability |
| **Situation Type** | Out-of-court TSA | Chapter 11 pre-packaged | Handles different restructuring types |
| **Distress Driver** | Supply-side (labor) | Demand-side (reimbursement) | Identifies root cause correctly |
| **Asset Type** | Asset-light | Asset-heavy | Adapts asset coverage analysis |
| **Capital Structure** | 4 tranches | 5 tranches | Handles variable complexity |
| **Resolution** | Take-private | Take-private | Identifies exit optionality |
| **Predictive Accuracy** | Base/bull cases realized | Base/bull cases realized | Validated predictive framework |

### Universal Distress Indicators (Both Cases)

1. **Going-Concern Disclosure:** Auditors flag material doubt 6-18 months before restructuring
2. **Leverage Elevation:** Debt/EBITDA >10x indicates severe distress
3. **Coverage Deterioration:** Interest coverage <1.0x indicates cash constraint
4. **Covenant Breaches:** Violation of financial covenants precedes restructuring
5. **Liquidity Pressure:** Revolver draws, declining cash balance
6. **Management Turnover:** Executive departures during distress period
7. **Equity Value Erosion:** Stock price decline or valuation pressure

### Predictive Validity

**ATI Physical Therapy (April 2023 → August 2025):**
- Predicted EBITDA: $25-35M FY2024 → Actual: ~$47M LTM (exceeded)
- Predicted Multiple: 7-11x → Actual: 11.2x (within range)
- Predicted EV: $210-550M → Actual: $523.3M (within range)
- Predicted Resolution: Take-private → Actual: Take-private (correct)

**Envision Healthcare (May 2023 → April 2024):**
- Predicted EBITDA: $485M stable → Actual: ~$485M LTM (met)
- Predicted Multiple: 7.5x → Actual: ~7.5x (met)
- Predicted EV: $3.6B → Actual: ~$3.6B (met)
- Predicted Resolution: Take-private → Actual: Take-private (correct)

See [`VALIDATION_METHODOLOGY.md`](VALIDATION_METHODOLOGY.md) for comprehensive validation
documentation and [`COMPARATIVE_ANALYSIS.md`](COMPARATIVE_ANALYSIS.md) for detailed
side-by-side comparison.

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
