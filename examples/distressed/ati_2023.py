"""ATI Physical Therapy (ATIP) — April 2023 Transaction Support Agreement.

Decision point: should a distressed-credit fund participate in the TSA, taking
part of the $25M new-money second-lien PIK-convertible facility plus some of
the $100M first-lien-to-second-lien exchange?

Why this example
----------------
Knighthead Capital and Marathon Asset Management (along with Advent, Caspian,
and Onex) built their ~98.6% pre-announcement equity stake across the 2023 TSA
and subsequent PIK-convertible tranches, culminating in the August 1, 2025
take-private at $2.85/share and a $523.3M TEV — roughly 11.2x LTM Adj EBITDA.

The interesting analytical question is the *entry* in April 2023, not the exit.
At entry, TTM EBITDA had collapsed from $39.8M (2021) to $6.7M (2022) — an 83%
drop — and the Feb 2022 $550M HPS-led credit facility was in covenant
distress. The TSA was a loan-to-own: new money plus a face-value exchange into
a second-lien PIK convertible that converts to post-reorg equity on a cramdown
or exit event.

Run
---
    python -m examples.distressed.ati_2023

Requires an LLM API key (``ANTHROPIC_API_KEY`` or ``OPENAI_API_KEY``) with
``QUANTAI_AGENT_MODEL`` pointing at a compatible model. A pre-rendered sample
output is checked in at ``ati_2023_memo.md`` for readers without a key.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from examples.distressed.agents import (
    CapitalStructureTranche,
    Situation,
    run_credit_committee,
)

logger = logging.getLogger(__name__)


def build_ati_situation() -> Situation:
    """Real-money situation as of the April 11, 2023 TSA signing.

    All numbers sourced from ATI 10-K FY2022, 10-Q Q1 2023, 8-K 04/21/2023,
    8-K 06/15/2023, DEF 14A 05/01/2023, and company press releases. See
    ``ati_2023_memo.md`` for the full citation list.
    """

    cap_structure = [
        CapitalStructureTranche(
            name="Super-priority Revolver",
            face_amount_mm=50.0,
            coupon="SOFR + ~500 drawn",
            maturity="Feb 2027",
            seniority=1,
            holder="HPS Investment Partners (Lender Rep)",
        ),
        CapitalStructureTranche(
            name="1L Senior Secured Term Loan",
            face_amount_mm=500.0,
            coupon="SOFR + 725",
            maturity="Feb 2028",
            seniority=2,
            holder="HPS Investment Partners (Lender Rep)",
        ),
        CapitalStructureTranche(
            name="Series A Senior Preferred Stock (2022)",
            face_amount_mm=165.0,
            coupon="8% cash / 10% PIK at issuer option",
            maturity="Perpetual",
            seniority=3,
            holder="Advent International + other SPAC-era investors",
        ),
    ]

    # Post-TSA, the new 2L PIK convertible layer will insert between 1L Term
    # Loan (reduced by $100M) and the Series A Preferred. We include the
    # prospective tranche here for clarity — it is the instrument we would
    # underwrite.
    cap_structure.append(
        CapitalStructureTranche(
            name="NEW — 2L PIK Convertible Notes (TSA)",
            face_amount_mm=125.0,  # $25M new money + $100M exchanged from 1L
            coupon="8% PIK",
            maturity="Aug 2028",
            seniority=2,  # senior to Preferred, subordinate to 1L Term Loan
            holder="TSA participants (prospective)",
        )
    )

    timeline = [
        {
            "date": "2021-06",
            "event": "FVAC II SPAC merger with ATI closes; $1.9B enterprise value at deal. Over-leveraged for the PT macro that follows.",
        },
        {
            "date": "2022-02-24",
            "event": "Refinances into $550M credit facility led by HPS Investment Partners ($500M 1L TL + $50M SP Revolver). Issues $165M Series A Senior Preferred concurrently.",
        },
        {
            "date": "2022-FY",
            "event": "Revenue $635.7M (+1% YoY). Adj EBITDA collapses to $6.7M (margin 1.1%) from $39.8M / 6.3% in 2021. Primary driver: PT wage inflation and therapist attrition (can't staff clinics to meet demand).",
        },
        {
            "date": "2023-Q1",
            "event": "Going-concern language in 10-Q. Stockholders' equity down to ~$20.5M at 3/31/2023. Covenants under 2022 Credit Agreement under pressure.",
        },
        {
            "date": "2023-04-11",
            "event": "Transaction Support Agreement signed. $25M new-money 2L PIK convertible + $100M of 1L exchanged into 2L PIK convertibles. 1-for-50 reverse stock split proposed.",
        },
        {"date": "2023-04-21", "event": "8-K filed describing TSA mechanics."},
        {
            "date": "2023-05-01",
            "event": "DEF 14A proxy filed for shareholder vote on TSA and reverse split.",
        },
        {
            "date": "DECISION_POINT",
            "event": "THIS IS THE COMMITTEE MEETING — should we participate in the TSA as a 2L PIK convertible holder?",
        },
    ]

    operating_metrics = {
        "FY2022 Revenue": "$635.7M (+1% YoY)",
        "FY2022 Adj EBITDA": "$6.7M (margin 1.1%; down from $39.8M / 6.3% in 2021)",
        "Q1 2023 Stockholders' equity": "~$20.5M",
        "Clinic count (end-2022)": "~923",
        "States covered": "~24",
        "Payor mix (highlight)": "Workers' comp franchise (legacy since 1996) — margin-accretive differentiator vs pure-play PT peers",
        "Market size (US outpatient PT)": "~$53B fragmented; top 6 chains ~9.7% of clinics",
        "Going-concern disclosure": "YES — material doubt flagged by auditors",
        "SPAC litigation": "Pending (settled Sep 2024 for $31M — not known at TSA time)",
    }

    known_risks = [
        "PT wage inflation could persist or accelerate, keeping EBITDA sub-$15M",
        "1L Term Loan remains ahead of us at $400M post-exchange; we are structurally junior to $450M of secured debt + revolver",
        "Workers' comp reimbursement policy is state-by-state — any adverse change in IL/TX/PA would hit disproportionately",
        "NYSE listing rules — reverse stock split buys time; a second compliance issue would delist",
        "SPAC-era securities class action is unresolved; damages could impair junior capital",
        "Sector consolidation thesis requires access to capital we may not have after a second distress leg",
        "Cramdown / Chapter 11 re-engagement if Q2/Q3 2023 does not show EBITDA recovery",
    ]

    return Situation(
        company="ATI Physical Therapy",
        ticker="ATIP",
        sector="Outpatient physical therapy / healthcare services",
        situation_type="Out-of-court restructuring (Transaction Support Agreement)",
        thesis_one_liner=(
            "Loan-to-own via 2L PIK convertible in a margin-compressed but recoverable outpatient PT platform, "
            "entering at a structurally distressed moment with asymmetric equity upside on PT wage normalization."
        ),
        timeline=timeline,
        capital_structure=cap_structure,
        operating_metrics=operating_metrics,
        current_position="No existing exposure — new underwrite",
        key_risks=known_risks,
    )


async def main() -> None:
    """Run the 4-agent credit committee and write the output memo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    situation = build_ati_situation()
    print(f"\nRunning credit committee on {situation.company} ...\n")
    result = await run_credit_committee(situation)

    out_path = Path(__file__).resolve().parent / "ati_2023_live_memo.md"
    out_path.write_text(result.rendered_memo())
    print(f"\nMemo written to {out_path}")
    print(f"Total LLM tokens used: {result.total_tokens:,}")


if __name__ == "__main__":
    asyncio.run(main())
