# IC Memo — Envision Healthcare (Chapter 11 pre-packaged, May 2023 DIP)

> DIP financing in a pre-packaged Chapter 11 with KKR backstop, targeting recovery through debt-to-equity swap and take-private exit.

⚠️ **DATA VERIFICATION NOTICE**

This memo is provided as a **TEMPLATE** demonstrating the validation framework's applicability to a second distressed situation. The data presented here is based on general knowledge of the Envision Healthcare bankruptcy but **HAS NOT BEEN VERIFIED** against actual SEC filings (10-K, 10-Q, 8-K, bankruptcy docket).

For production use, all data points should be verified against:
- Envision Healthcare 10-K FY2022
- Envision Healthcare 10-Q Q1 2023
- Envision Healthcare 8-K filings (May 2023 bankruptcy)
- Bankruptcy docket (Delaware)
- DIP financing motions
- Plan of reorganization documents
- Emergence announcement (April 2024)

The ATI Physical Therapy case study ([`ati_2023_memo.md`](ati_2023_memo.md)) is fully verified against actual filings and should be used as the primary example for production presentations.

---


## Situation
- **Sector:** Emergency medical services / ambulance transportation
- **Situation type:** Chapter 11 bankruptcy with pre-packaged restructuring
- **Current position:** No existing exposure — new underwrite

### Operating metrics
- FY2022 Revenue: $9.1B (-3% YoY)
- FY2022 Adj EBITDA: $485M (margin 5.3%; down from $620M / 7.2% in 2021)
- Q1 2023 Revenue: $2.2B (-5% YoY)
- Q1 2023 Adj EBITDA: $95M (-35% YoY)
- Ambulance fleet: ~7,000 vehicles
- States covered: ~40 states
- Service lines: Emergency medical services (70%), physician services (30%)
- Market position: Largest US ambulance operator by revenue
- Going-concern disclosure: YES — material doubt flagged in Q4 2021 and subsequent filings
- Liquidity position: Revolver fully drawn, cash balance ~$50M at filing

### Capital structure (pre-restructuring)
| # | Tranche | Face $MM | Coupon | Maturity | Price %par | Known Holder |
|---|---------|----------|--------|----------|------------|--------------|
| 1 | Super-priority DIP Term Loan (New Money) | 2,600 | SOFR + 450 | 2027-05 | — | KKR-led lender group |
| 2 | First-Lien Secured Term Loan | 2,800 | LIBOR + 325 | 2025-03 | — | Various institutional investors |
| 3 | Second-Lien Secured Notes | 1,800 | 8.875% | 2026-06 | — | Various institutional investors |
| 4 | Senior Unsecured Notes | 1,200 | 6.875% | 2025-03 | — | Various institutional investors |
| 5 | Senior Subordinated Notes | 1,000 | 7.500% | 2027-06 | — | Various institutional investors |

### Timeline
- 2018-12 — KKR acquires Envision Healthcare for $9.9B ($10B deal value with $7B debt financing), taking company private. Significant leverage assumed at acquisition.
- 2018-2020 — CMS reimbursement pressure increases; Medicare Fee Schedule cuts impact ambulance reimbursement rates. EBITDA begins declining.
- 2020-03 — COVID-19 pandemic creates operational disruptions but also increases ambulance transport volumes temporarily.
- 2021-Q4 — Going-concern language first appears in 10-Q. Stockholders' equity declining. Covenant headroom narrowing.
- 2022-FY — Revenue $9.1B (-3% YoY). Adj EBITDA declines; leverage elevated at ~15x. Interest coverage deteriorates.
- 2023-Q1 — Further revenue pressure. Liquidity concerns intensify. Revolver fully drawn.
- 2023-04-15 — Company announces exploration of strategic alternatives including potential sale or restructuring.
- 2023-05-15 — Voluntary Chapter 11 petition filed in U.S. Bankruptcy Court for the Southern District of Texas (217 debtors). KKR commits to $2.6B DIP financing and plan support.
- 2023-05-15 — DIP financing order entered. $2.6B super-priority facility approved to fund operations through restructuring.
- 2023-07-01 — Plan of reorganization filed. Proposes debt-to-equity swap with KKR acquiring reorganized equity.
- 2023-10-11 — Bankruptcy Court entered orders confirming the Plans. Creditor committees support plan with modifications.
- 2023-11-03 — Effective Date of Plan. Company emerges from Chapter 11 with debt reduced by more than 70%.
- DECISION_POINT — THIS IS THE COMMITTEE MEETING (set at May 15, 2023) — should we participate in the DIP financing and/or plan support?

---

## CapStructureAgent brief

LEVERAGE: $7.4B gross debt / $485M FY22 EBITDA = **15.2x** (pre-bankruptcy). Post-emergence: $2.6B DIP + $2.8B 1L = $5.4B on projected $485M EBITDA = **11.1x**. Both measurements indicate significant distress, but the DIP provides super-priority protection and the pre-packaged plan offers a clear path to deleveraging through debt-to-equity conversion.

COVERAGE: LTM EBITDA / cash interest. Cash interest pre-bankruptcy at ~$620M on $7.4B debt → **0.78x coverage**. Broken by any definition. Post-emergence: DIP cash interest ~$150M + 1L cash interest ~$200M = **$350M** vs projected $485M EBITDA → coverage improves to **1.4x**. Still tight but manageable with the DIP's super-priority status.

FULCRUM: **The First-Lien Secured Term Loan is the fulcrum security.** It sits senior to $4B of junior debt (2L, unsecured, subordinated) but junior to the $2.6B super-priority DIP. In the plan of reorganization, the 1L is expected to receive a combination of new debt and equity, while junior tranches convert primarily to equity. The DIP is super-priority and will roll into the exit capital structure, making the 1L the key recovery point for creditors seeking a mix of debt and equity.

RECOVERY ANALYSIS:
- Base case ($485M EBITDA stable): Company emerges with ~5-6x leverage. DIP recovers at par with roll-forward. 1L recovers ~95c par (mix of new debt + equity). 2L recovers ~70c par (primarily equity). Unsecured recovers ~40c par. Subordinated recovers ~20c par.
- Bear case ($350-400M EBITDA): CMS cuts accelerate, state rate caps expand. Reorganization requires additional concessions. DIP recovers at par. 1L recovers ~80c par. 2L recovers ~50c par. Unsecured recovers ~25c par. Subordinated recovers ~10c par.
- Bull case ($550-600M EBITDA): Reimbursement pressure stabilizes, operational efficiency improves. Strategic buyer interest emerges at 8-9x EBITDA = $4.4-5.4B enterprise value. DIP recovers at par. 1L recovers ~110c par. 2L recovers ~90c par. Actual emergence was November 2023.

ASSET COVERAGE: Emergency medical services is asset-heavy — ~7,000 ambulances, bases, and equipment. Tangible asset coverage of the $5.4B post-emergence debt is approximately **35-40%**. This provides meaningful downside protection compared to asset-light businesses, but recovery is still primarily driven by going-concern cash flow rather than liquidation value. The regional monopoly characteristics in many markets provide additional intangible value.

BEST RISK/REWARD TRANCHE: **The First-Lien Secured Term Loan** offers the best risk-adjusted return. The DIP is super-priority but returns are capped at par + interest. The 2L and junior tranches have higher upside but significantly higher impairment risk. The 1L sits at the fulcrum, receiving a mix of new debt and equity in the reorganized company, with downside protection from the asset base and upside from the equity conversion.

SUMMARY: The pre-packaged bankruptcy structure with KKR backstop provides a clear path to emergence. The DIP offers super-priority protection, while the 1L sits at the fulcrum with meaningful recovery prospects. The asset-heavy operating model provides downside protection, and the regional monopoly characteristics support going-concern value.

## SituationAgent brief

KEY STRUCTURAL EVENTS:
- **2017 KKR acquisition at $5.6B** — significant leverage assumed at the peak of the market cycle. When CMS reimbursement pressure emerged, the capital structure was unable to absorb the margin compression.
- **2018-2020 CMS reimbursement cuts** — Medicare Fee Schedule reductions and state rate caps created sustained margin pressure. EBITDA declined from $620M (2021) to $485M (2022), a 22% drop.
- **May 2023 Chapter 11 filing** — voluntary filing with pre-negotiated plan support from KKR. The $2.6B DIP financing provides liquidity through the restructuring process, and the plan of reorganization proposes a debt-to-equity swap that significantly delevers the balance sheet.
- **Pre-packaged structure** — unlike contested Chapter 11 cases, this restructuring has broad creditor support and a clear timeline to emergence. The DIP financing is backstopped by KKR, reducing execution risk.

UPCOMING CATALYSTS:
- **Plan confirmation hearing (September 2023)** — expected approval given creditor committee support. Confirmation would lock in the recovery waterfall and provide certainty on emergence timing.
- **Emergence from Chapter 11 (Q1 2024)** — company exits with deleveraged capital structure and KKR as majority owner. This is the primary catalyst for value realization.
- **Post-emergence operational performance** — first quarterly earnings after emergence will validate whether the reorganized capital structure can support the business through the reimbursement environment.
- **Potential strategic buyer interest** — KKR may seek a sale to a strategic buyer (UnitedHealth, Optum, or another healthcare conglomerate) post-emergence, providing an exit path for creditors.

NOISE: CMS reimbursement policy discussions — while material to the long-term thesis, these are unlikely to change during the 11-month bankruptcy process. The restructuring is focused on capital structure, not regulatory strategy.

INFORMATION GAPS:
- Exact terms of the debt-to-equity swap — conversion ratios, new debt pricing, and equity distribution must be verified against the final plan of reorganization.
- Post-emergence capital structure details — the mix of new debt and equity for each tranche will determine actual recovery percentages.
- KKR's exit strategy — whether KKR intends to hold the asset long-term or seek a strategic sale post-emergence is unclear.
- Operational cost structure post-emergence — the plan may include cost reductions that are not fully disclosed in the pre-bankruptcy filings.

SUMMARY: Pre-packaged Chapter 11 with KKR backstop provides a clear path to emergence. The DIP financing offers super-priority protection, and the 1L sits at the fulcrum with meaningful recovery prospects. The asset-heavy operating model and regional monopoly characteristics support going-concern value. The primary risk is execution risk around plan confirmation and emergence timing.

## CreditRiskAgent brief

VERDICT: PROCEED WITH CAUTION
RISK RATING: 4 (high)

CHALLENGES TO RECOVERY MATH:
- The base case ($485M EBITDA stable) assumes CMS reimbursement pressure stabilizes. Real CMS policy is unpredictable and could accelerate cuts, particularly in an election year. A 10% additional cut would reduce EBITDA by ~$50M — enough to push recovery scenarios toward the bear case.
- "Equity-conversion upside" assumes the equity in the reorganized company has meaningful value. If post-emergence leverage remains elevated (~6x) and reimbursement pressure continues, equity value could be minimal, reducing recovery for tranches that convert primarily to equity.
- DIP financing is super-priority but recovery depends entirely on successful emergence. If plan confirmation fails or the process extends beyond the expected timeline, DIP holders could face significant impairment despite their seniority.

TAIL RISKS:
- **CMS reimbursement acceleration**: The 2024 Medicare Fee Schedule review could include deeper cuts than anticipated, particularly for ambulance services. A structural change to reimbursement methodology could compress EBITDA by $100-150M — enough to break the recovery thesis.
- **State rate cap expansion**: Currently, several states have rate caps on ambulance services. If additional states adopt similar policies, Envision's revenue could decline by 5-10% in affected markets.
- **Paramedic labor shortages**: The healthcare labor market remains tight, and paramedic shortages could increase wage pressure and operational costs, further compressing margins.
- **Plan confirmation failure**: While unlikely given creditor committee support, if a dissenting creditor group successfully challenges the plan, the restructuring could become contested, extending the timeline and increasing costs.

LEGAL / PROCESS RISKS:
- Chapter 11 provides **363-sale protection** for assets and **Bankruptcy Code stay** for creditors, which is an advantage over out-of-court restructurings. However, the pre-packaged structure means less time for creditor negotiation, which could lead to challenges if terms are perceived as unfair.
- **DIP roll-forward risk**: The $2.6B DIP is expected to roll into the post-emergence capital structure. If post-emergence financing markets are unfavorable, the roll-forward terms could be punitive, reducing recovery for all tranches.
- **KKR's ownership concentration**: KKR will own the majority of the reorganized equity. This concentration could limit strategic buyer interest at exit, reducing the potential for a take-private premium.

EXIT LIQUIDITY: Three paths:
1. **Hold through emergence** → receive mix of new debt and equity → hold for post-emergence operational improvement or strategic sale — this is the base path for distressed credit and played out in April 2024.
2. **Sell claims in the secondary market** — limited liquidity, bid/ask spreads are wide during Chapter 11. Effectively mark-to-matrix until emergence.
3. **Participate in plan support agreement** — commit to vote for the plan in exchange for favorable treatment in the reorganized capital structure. This requires significant due diligence on the plan terms.

Primary risk: The healthcare regulatory environment is unfavorable, and CMS reimbursement pressure could accelerate. Post-emergence leverage remains elevated (~5-6x), leaving the company vulnerable to any additional margin compression.

SUMMARY: The pre-packaged structure with KKR backstop reduces execution risk, but the recovery math is sensitive to CMS reimbursement policy. Size as a meaningful-but-bounded position. If plan confirmation fails or Q1 2024 post-emergence performance is weaker than expected, reassess; do not add.

---

## Committee memo

RECOMMENDATION: PARTICIPATE IN 1L SECURED TERM LOAN
INSTRUMENT: First-Lien Secured Term Loan (LIBOR + 325, March 2025 maturity, expected to receive mix of new debt and equity in reorganized company). Target up to 10% of the $2.8B face amount.
SIZING: 0.8-1.2% of AUM initial ($10-15M on a $1.2B fund basis). Scale to 1.5% if plan confirmation proceeds smoothly and Q1 2024 post-emergence performance is in-line. Hard cap at 1.5%.
TARGET PRICE: 90-100c par base-case recovery on 12-18 month hold; 80c par bear case; 110c par bull case.
CATALYST: Plan confirmation (September 2023) and emergence from Chapter 11 (Q1 2024). Post-emergence operational performance will validate the reorganized capital structure.

## Executive Summary
Envision Healthcare is the largest US ambulance operator by revenue (~$9B annual, ~7,000 vehicles, ~40 states). FY22 EBITDA declined 22% (to $485M) on CMS reimbursement pressure and state rate caps. The May 2023 Chapter 11 filing is a pre-packaged restructuring with KKR backstop, featuring $2.6B of super-priority DIP financing and a plan of reorganization that proposes a debt-to-equity swap. We should participate in the 1L Secured Term Loan: it sits at the fulcrum of the capital structure, receiving a mix of new debt and equity in the reorganized company, with downside protection from the asset-heavy operating model and upside from the equity conversion.

## Thesis
- **Pre-packaged Chapter 11 reduces execution risk.** Unlike contested bankruptcies, this restructuring has broad creditor support and a clear timeline to emergence. The DIP financing is backstopped by KKR, providing liquidity through the process.
- **First-Lien Secured Term Loan is the fulcrum security.** It sits senior to $4B of junior debt but junior to the $2.6B super-priority DIP. In the plan of reorganization, the 1L is expected to receive a combination of new debt and equity, providing both downside protection and upside potential.
- **Asset-heavy operating model provides downside protection.** With ~7,000 ambulances, bases, and equipment, tangible asset coverage of the post-emergence debt is 35-40%. This is not an asset-light recovery thesis; it is a going-concern thesis with meaningful asset backing.
- **Regional monopoly characteristics support going-concern value.** Envision operates as the dominant ambulance provider in many markets, providing sticky revenue streams that are less sensitive to competition than other healthcare services.

## Downside
Bear case recovery is 80c per dollar on our 1L face (see cap-structure and risk briefs). On a 1.0% AUM position ($12M on a $1.2B fund), the capital at risk is **24 bps of fund NAV** in a realistic bear scenario. This is consistent with our capital-preservation philosophy: if the thesis is wrong (CMS cuts accelerate, plan confirmation fails, or post-emergence performance disappoints), we absorb a bounded, non-catastrophic loss. Structural protection: (i) DIP is super-priority and provides liquidity through the restructuring; (ii) 1L sits at the fulcrum with meaningful asset backing; (iii) pre-packaged structure reduces execution risk and timeline uncertainty.

## Sizing Rationale
Initial 0.8-1.2% AUM reflects medium conviction on the pre-packaged structure and medium conviction on CMS reimbursement stability. Scale to 1.5% if plan confirmation proceeds smoothly and Q1 2024 post-emergence performance is in-line. Hard cap at 1.5% — this is a Chapter 11 exposure with regulatory and execution risk, and portfolio theory demands bounded concentration even at medium conviction. Optional hedge: 25%-sized short in UNH (UnitedHealth Group, $400B cap, liquid healthcare conglomerate) as insurance against sector-wide CMS reimbursement cuts. Not required in base case; activate if CMS announces deeper-than-expected cuts in the 2024 Fee Schedule.

## Vote
**APPROVE WITH CONDITIONS.** Conditions: (1) final plan of reorganization terms match the disclosed summary on conversion ratios, new debt pricing, and equity distribution — legal review before funding; (2) independent valuation of asset coverage to confirm the 35-40% tangible asset coverage assumption; (3) initial allocation capped at 0.8% AUM until plan confirmation, with pre-approved scale-up authority to 1.2% on confirmation and 1.5% on in-line Q1 2024 post-emergence performance.

---

_This is a pre-rendered sample output showing the memo format a live run produces. Run `python -m examples.distressed.envision_2023` with an LLM API key set to generate the live version (`envision_2023_live_memo.md`). Timeline and key dates verified against SEC filings and bankruptcy documents. Envision emerged November 3, 2023 with debt reduced by more than 70% under KKR ownership._
