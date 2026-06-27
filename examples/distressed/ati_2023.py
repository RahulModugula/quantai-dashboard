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

from examples.distressed.agents import run_credit_committee
from examples.distressed.models import Situation

logger = logging.getLogger(__name__)

# The ATI situation now lives in a YAML file so it can be edited without touching
# Python and serves as the worked example for the `quantai-credit` CLI. This
# function loads it, keeping a single source of truth.
ATI_SITUATION_PATH = Path(__file__).resolve().parent / "situations" / "ati_2023.yaml"


def build_ati_situation() -> Situation:
    """Real-money situation as of the April 11, 2023 TSA signing.

    All numbers sourced from ATI 10-K FY2022, 10-Q Q1 2023, 8-K 04/21/2023,
    8-K 06/15/2023, DEF 14A 05/01/2023, and company press releases. The data
    lives in ``situations/ati_2023.yaml``; see ``ati_2023_memo.md`` for the
    full citation list.
    """
    return Situation.from_file(ATI_SITUATION_PATH)


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
