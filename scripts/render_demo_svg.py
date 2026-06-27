#!/usr/bin/env python3
"""Render a `quantai-credit run` terminal session to a committable SVG.

The SVG renders inline on GitHub (no browser or dashboard run needed) and is the
hero image for the README. Regenerate it with:

    python scripts/render_demo_svg.py

Requires `rich` (pip install rich). Content is sourced from the committed ATI
memo (examples/distressed/ati_2023_memo.md) so the asset is stable.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

OUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "credit_committee_demo.svg"


def render() -> None:
    console = Console(record=True, width=92)

    console.print(
        "[bright_black]$[/] [bold]quantai-credit run[/] examples/distressed/situations/ati_2023.yaml"
    )
    console.print(
        "[bright_black]Running 4-agent credit committee on[/] [bold]ATI Physical Therapy[/] [bright_black]...[/]"
    )
    console.print()
    console.print(
        "  [green]✓[/] [cyan]CapStructureAgent[/]     leverage [bold]82.1x[/] · coverage [bold]0.11x[/] · fulcrum: [yellow]2L PIK Convertible[/]"
    )
    console.print(
        "  [green]✓[/] [cyan]SituationAgent[/]        supply-side EBITDA shock · catalyst: [yellow]Q3'23 print[/]"
    )
    console.print(
        "  [green]✓[/] [cyan]CreditRiskAgent[/]       VERDICT: [yellow]PROCEED WITH CAUTION[/] · RISK [bold]4/5[/]"
    )
    console.print(
        "  [green]✓[/] [cyan]CreditCommitteeAgent[/]  memo → [bright_black]ati_physical_therapy_memo.md[/]"
    )
    console.print()
    console.print(
        "[bright_black]──────────────────────────────────────────────────────────────────────────[/]"
    )
    console.print(
        "  [bold white]IC MEMO — ATI Physical Therapy[/]  [bright_black](Out-of-court restructuring / TSA)[/]"
    )
    console.print(
        "[bright_black]──────────────────────────────────────────────────────────────────────────[/]"
    )
    console.print("  [bold green]RECOMMENDATION[/]  [bold green]BUY[/]")
    console.print(
        "  [bold green]INSTRUMENT[/]      2L PIK Convertible Notes (8% PIK, Aug 2028) — [yellow]fulcrum security[/]"
    )
    console.print(
        "  [bold green]SIZING[/]          1.0–1.5% AUM, scale to 2.0% on Q3'23 EBITDA > $25M run-rate"
    )
    console.print(
        "  [bold green]TARGET PRICE[/]    140–180c par base · [bold]250–320c bull[/] · 55–70c bear"
    )
    console.print(
        "  [bold green]CATALYST[/]        PT wage normalization → EBITDA recovery (BLS data turning)"
    )
    console.print("  [bold yellow]VOTE[/]            APPROVE WITH CONDITIONS")
    console.print()
    console.print(
        "  [bright_black]Outcome (Aug 2025):[/] [green]$523.3M take-private @ ~11.2x EBITDA — base/bull thesis confirmed[/]"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    console.save_svg(str(OUT), title="quantai-credit")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    render()
