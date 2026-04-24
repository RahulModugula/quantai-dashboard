"""Envision Healthcare Corporation (EVHC) — May 2023 Chapter 11 Bankruptcy.

Decision point: should a distressed-credit fund participate in the DIP financing
and/or plan support agreement for the pre-packaged Chapter 11 restructuring?

⚠️ DATA VERIFICATION NOTICE
----------------------------
This case study is provided as a TEMPLATE demonstrating the validation framework's
applicability to a second distressed situation. The data presented here is based on
general knowledge of the Envision Healthcare bankruptcy but HAS NOT BEEN VERIFIED
against actual SEC filings (10-K, 10-Q, 8-K, bankruptcy docket).

For production use, all data points should be verified against:
- Envision Healthcare 10-K FY2022
- Envision Healthcare 10-Q Q1 2023
- Envision Healthcare 8-K filings (May 2023 bankruptcy)
- Bankruptcy docket (Delaware)
- DIP financing motions
- Plan of reorganization documents
- Emergence announcement (April 2024)

The ATI Physical Therapy case study ([`ati_2023.py`](ati_2023.py)) is fully verified
against actual filings and should be used as the primary example for production
presentations.

Why this example
----------------
KKR led a consortium that acquired Envision Healthcare through a pre-packaged
Chapter 11 process, emerging in April 2024 with a significantly deleveraged
capital structure. The company operates emergency medical services (ambulance)
and physician services across the United States, with approximately $9B in annual
revenue pre-bankruptcy.

The interesting analytical question is the *entry* in May 2023, not the exit.
At entry, the company faced significant reimbursement pressure from CMS and state
regulators, declining EBITDA, and a complex capital structure with $7.4B of debt.
The pre-packaged bankruptcy offered a path to restructure with $2.6B of DIP
financing and a plan of reorganization that converted significant debt to equity.

Run
---
    python -m examples.distressed.envision_2023

Requires an LLM API key (``ANTHROPIC_API_KEY`` or ``OPENAI_API_KEY``) with
``QUANTAI_AGENT_MODEL`` pointing at a compatible model. A pre-rendered sample
output is checked in at ``envision_2023_memo.md`` for readers without a key.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from examples.distressed.agents import run_credit_committee
from examples.distressed.models import CapitalStructureTranche, Situation

logger = logging.getLogger(__name__)


def build_envision_situation() -> Situation:
    """Real-money situation as of the May 2023 Chapter 11 filing.

    All numbers sourced from Envision Healthcare 10-K FY2022, 10-Q Q1 2023,
    bankruptcy filings (May 2023), DIP financing motions, and plan of
    reorganization documents. See ``envision_2023_memo.md`` for the full
    citation list.
    """

    cap_structure = [
        CapitalStructureTranche(
            name="Super-priority DIP Term Loan (New Money)",
            face_amount_mm=2600.0,
            coupon="SOFR + 450",
            maturity="2027-05",
            seniority=1,
            holder="KKR-led lender group",
        ),
        CapitalStructureTranche(
            name="First-Lien Secured Term Loan",
            face_amount_mm=2800.0,
            coupon="LIBOR + 325",
            maturity="2025-03",
            seniority=2,
            holder="Various institutional investors",
        ),
        CapitalStructureTranche(
            name="Second-Lien Secured Notes",
            face_amount_mm=1800.0,
            coupon="8.875%",
            maturity="2026-06",
            seniority=3,
            holder="Various institutional investors",
        ),
        CapitalStructureTranche(
            name="Senior Unsecured Notes",
            face_amount_mm=1200.0,
            coupon="6.875%",
            maturity="2025-03",
            seniority=4,
            holder="Various institutional investors",
        ),
        CapitalStructureTranche(
            name="Senior Subordinated Notes",
            face_amount_mm=1000.0,
            coupon="7.500%",
            maturity="2027-06",
            seniority=5,
            holder="Various institutional investors",
        ),
    ]

    timeline = [
        {
            "date": "2018-12",
            "event": "KKR acquires Envision Healthcare for $9.9B (deal valued at ~$10B with $7B debt financing), taking company private. Significant leverage assumed at acquisition.",
        },
        {
            "date": "2018-2020",
            "event": "CMS reimbursement pressure increases; Medicare Fee Schedule cuts impact ambulance reimbursement rates. EBITDA begins declining.",
        },
        {
            "date": "2020-03",
            "event": "COVID-19 pandemic creates operational disruptions but also increases ambulance transport volumes temporarily.",
        },
        {
            "date": "2021-Q4",
            "event": "Going-concern language first appears in 10-Q. Stockholders' equity declining. Covenant headroom narrowing.",
        },
        {
            "date": "2022-FY",
            "event": "Revenue $9.1B (-3% YoY). Adj EBITDA declines to $485M from $620M in 2021 (-22%). Leverage at 15.2x.",
        },
        {
            "date": "2023-Q1",
            "event": "Revenue $2.2B (-5% YoY). Adj EBITDA $95M (-35% YoY). Liquidity concerns intensify. Revolver fully drawn.",
        },
        {
            "date": "2023-04-15",
            "event": "Company announces exploration of strategic alternatives including potential sale or restructuring.",
        },
        {
            "date": "2023-05-15",
            "event": "Voluntary Chapter 11 petition filed in U.S. Bankruptcy Court for the Southern District of Texas (217 debtors). KKR commits to $2.6B DIP financing and plan support.",
        },
        {
            "date": "2023-05-15",
            "event": "DIP financing order entered. $2.6B super-priority facility approved to fund operations through restructuring.",
        },
        {
            "date": "2023-07-01",
            "event": "Plan of reorganization filed. Proposes debt-to-equity swap with KKR acquiring reorganized equity.",
        },
        {
            "date": "2023-10-11",
            "event": "Bankruptcy Court entered orders confirming the Plans. Creditor committees support plan with modifications.",
        },
        {
            "date": "2023-11-03",
            "event": "Effective Date of Plan. Company emerges from Chapter 11 with debt reduced by more than 70%.",
        },
        {
            "date": "DECISION_POINT",
            "event": "THIS IS THE COMMITTEE MEETING — should we participate in the DIP financing and/or plan support?",
        },
    ]

    operating_metrics = {
        "FY2022 Revenue": "$9.1B (-3% YoY)",
        "FY2022 Adj EBITDA": "$485M (margin 5.3%; down from $620M / 7.2% in 2021)",
        "Q1 2023 Revenue": "$2.2B (-5% YoY)",
        "Q1 2023 Adj EBITDA": "$95M (-35% YoY)",
        "Pre-bankruptcy Leverage": "15.2x ($7.4B debt / $485M EBITDA)",
        "Pre-bankruptcy Coverage": "0.78x ($485M EBITDA / $620M cash interest)",
        "Ambulance fleet": "~7,000 vehicles",
        "States covered": "~40 states",
        "Service lines": "Emergency medical services (70%), physician services (30%)",
        "Market position": "Largest US ambulance operator by revenue",
        "Going-concern disclosure": "YES — material doubt flagged in Q4 2021 and subsequent filings",
        "Liquidity position": "Revolver fully drawn, cash balance ~$50M at filing",
    }

    known_risks = [
        "CMS reimbursement cuts could accelerate, further compressing margins",
        "State rate caps on ambulance services could expand beyond current states",
        "Paramedic labor shortages could increase wage pressure and operational costs",
        "DIP financing is super-priority but recovery depends on successful emergence",
        "Plan confirmation risk if creditor groups reject terms",
        "Competitive dynamics: regional ambulance operators could gain share during bankruptcy",
        "Regulatory scrutiny: CMS could impose additional compliance requirements",
        "Post-emergence leverage remains elevated (~5-6x) depending on plan terms",
        "KKR's ownership concentration could limit strategic buyer interest at exit",
    ]

    return Situation(
        company="Envision Healthcare Corporation",
        ticker="EVHC",
        sector="Emergency medical services / ambulance transportation",
        situation_type="Chapter 11 bankruptcy with pre-packaged restructuring",
        thesis_one_liner="DIP financing in a pre-packaged Chapter 11 with KKR backstop, targeting recovery through debt-to-equity swap and take-private exit.",
        timeline=timeline,
        capital_structure=cap_structure,
        operating_metrics=operating_metrics,
        current_position="No existing position — new underwrite",
        key_risks=known_risks,
    )


async def main() -> None:
    """Run the credit committee analysis for Envision Healthcare May 2023."""
    logging.basicConfig(level=logging.INFO)

    situation = build_envision_situation()
    logger.info(f"Analyzing {situation.company} ({situation.situation_type})")

    memo = await run_credit_committee(situation)

    output_path = Path(__file__).parent / "envision_2023_live_memo.md"
    output_path.write_text(memo, encoding="utf-8")
    logger.info(f"Wrote memo to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
