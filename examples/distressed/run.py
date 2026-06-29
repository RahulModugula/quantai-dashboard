"""``quantai-credit`` — run an AI distressed-credit committee on any situation.

The credit committee (CapStructure + Situation -> CreditRisk -> Committee) is
data-agnostic: point it at a YAML/JSON file describing *any* distressed company
and it writes an IC-style vote memo.

    quantai-credit new my_deal.yaml       # scaffold a blank situation file
    quantai-credit validate my_deal.yaml  # free pre-flight snapshot (no LLM)
    quantai-credit run my_deal.yaml        # run the committee, write a memo + JSON
    quantai-credit list                    # show bundled example situations

`run` needs an LLM API key (any LiteLLM-supported provider). Set one of
ANTHROPIC_API_KEY / OPENAI_API_KEY / OPENROUTER_API_KEY, and optionally
QUANTAI_AGENT_MODEL to pick the model. `validate`/`new`/`list` are free.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
from pathlib import Path

from examples.distressed.models import Situation
from examples.distressed.snapshot import compute_snapshot

SITUATIONS_DIR = Path(__file__).resolve().parent / "situations"
TEMPLATE_PATH = SITUATIONS_DIR / "TEMPLATE.yaml"

_KEY_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
)

_DECISION_KEYS = ("RECOMMENDATION", "INSTRUMENT", "SIZING", "TARGET PRICE", "CATALYST")


def _has_api_key() -> bool:
    # Ollama runs locally with no key; treat an Ollama model as "keyed".
    model = os.environ.get("QUANTAI_AGENT_MODEL", "")
    if model.startswith("ollama/"):
        return True
    return any(os.environ.get(v) for v in _KEY_ENV_VARS)


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_") or "memo"


def _console():
    """Return a rich Console, or None if rich isn't installed (graceful)."""
    try:
        from rich.console import Console

        return Console(stderr=True)
    except ImportError:
        return None


def _parse_decision(memo_text: str) -> dict[str, str]:
    """Pull the committee's decision fields out of the memo's KEY: value lines."""
    out: dict[str, str] = {}
    for line in memo_text.splitlines():
        for key in _DECISION_KEYS:
            if line.strip().upper().startswith(key + ":"):
                out[key.lower().replace(" ", "_")] = line.split(":", 1)[1].strip()
    # The vote is the line after a "## Vote" heading or a "VOTE:" line.
    m = re.search(r"##\s*Vote\s*\n+([^\n]+)", memo_text, re.IGNORECASE)
    if m:
        out["vote"] = m.group(1).strip().strip("*").strip()
    return out


def _print_snapshot(snapshot, console) -> None:
    """Pretty-print the computed snapshot to stderr (rich if available)."""
    if console is not None:
        from rich.markdown import Markdown
        from rich.panel import Panel

        header = f"[bold]{snapshot.company}[/]  ·  {snapshot.num_tranches} tranches  ·  ${snapshot.total_debt_mm:,.0f}MM debt"
        if snapshot.leverage_x is not None and snapshot.leverage_x != float("inf"):
            header += f"  ·  [yellow]{snapshot.leverage_x:.1f}x[/] gross leverage"
        console.print(
            Panel(header, title="Cap-Structure Snapshot (computed, no LLM)", expand=False)
        )
        console.print(Markdown(snapshot.render_markdown()))
    else:
        print(snapshot.render_markdown(), file=sys.stderr)


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------


def cmd_new(args: argparse.Namespace) -> int:
    dest = Path(args.path)
    if dest.exists() and not args.force:
        print(f"refusing to overwrite existing file: {dest} (use --force)", file=sys.stderr)
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE_PATH, dest)
    print(f"Wrote situation template to {dest}")
    print(f"Edit it, then:  quantai-credit validate {dest}   # free pre-flight")
    print(f"          then:  quantai-credit run {dest}        # full committee")
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    files = sorted(p for p in SITUATIONS_DIR.glob("*.y*ml") if p.name != "TEMPLATE.yaml")
    if not files:
        print("No bundled situations found.")
        return 0
    print("Bundled example situations:\n")
    for p in files:
        try:
            s = Situation.from_file(p)
            label = f"{s.company} — {s.situation_type or 'situation'}"
            extra = (
                f" ({s.ltm_ebitda_mm and s.total_debt_mm / s.ltm_ebitda_mm:.0f}x lev)"
                if s.ltm_ebitda_mm
                else ""
            )
        except Exception as exc:  # noqa: BLE001 - listing must never hard-fail
            label, extra = f"(could not parse: {exc})", ""
        print(f"  {p.relative_to(SITUATIONS_DIR.parent.parent)}")
        print(f"      {label}{extra}\n")
    print("Run one with:  quantai-credit run <path>")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        situation = Situation.from_file(args.path)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        print(f"Could not load situation: {exc}", file=sys.stderr)
        return 1

    snapshot = compute_snapshot(situation)
    if args.json:
        print(json.dumps(snapshot.to_dict(), indent=2))
        return 0

    _print_snapshot(snapshot, _console())
    if snapshot.warnings:
        print(f"\n{len(snapshot.warnings)} completeness note(s) — see above.", file=sys.stderr)
    else:
        print("\nNo completeness issues found. Ready to run.", file=sys.stderr)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        situation = Situation.from_file(args.path)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        print(f"Could not load situation: {exc}", file=sys.stderr)
        return 1

    console = _console()
    snapshot = compute_snapshot(situation)
    _print_snapshot(snapshot, console)

    if not _has_api_key():
        print(
            "\nNo LLM API key found. The committee calls an LLM to write the memo.\n"
            "Set one of: " + ", ".join(_KEY_ENV_VARS) + "\n"
            "  (or QUANTAI_AGENT_MODEL=ollama/llama3 to run locally with no key)\n\n"
            "The snapshot above is free and needs no key. For a full sample memo:\n"
            "  python -m examples.distressed.demo",
            file=sys.stderr,
        )
        return 2

    # Imported lazily so `new`/`list`/`validate` work without litellm.
    from examples.distressed.agents import run_credit_committee

    print(f"\nRunning 4-agent credit committee on {situation.company} ...", file=sys.stderr)
    result = asyncio.run(run_credit_committee(situation))

    # The memo leads with the deterministic snapshot, then the agent briefs.
    memo = snapshot.render_markdown() + "\n\n---\n\n" + result.rendered_memo()
    decision = _parse_decision(result.committee_memo.content)

    stem = args.out_stem or _slug(situation.company)
    memo_path = Path(f"{stem}_memo.md")
    json_path = Path(f"{stem}.json")
    memo_path.write_text(memo)
    json_path.write_text(
        json.dumps(
            {
                "company": situation.company,
                "ticker": situation.ticker,
                "situation_type": situation.situation_type,
                "decision": decision,
                "snapshot": snapshot.to_dict(),
                "tokens": result.total_tokens,
                "memo_path": str(memo_path),
            },
            indent=2,
        )
    )

    # Decision summary
    if console is not None:
        from rich.table import Table

        table = Table(title=f"Committee decision — {situation.company}", show_header=False)
        for key in ("recommendation", "instrument", "sizing", "target_price", "catalyst", "vote"):
            if decision.get(key):
                table.add_row(f"[bold green]{key.replace('_', ' ').upper()}[/]", decision[key])
        console.print(table)
    else:
        for key in ("recommendation", "instrument", "sizing", "target_price", "catalyst", "vote"):
            if decision.get(key):
                print(f"{key.replace('_', ' ').upper()}: {decision[key]}", file=sys.stderr)

    print(f"\nMemo:  {memo_path}", file=sys.stderr)
    print(f"JSON:  {json_path}", file=sys.stderr)
    print(f"Tokens used: {result.total_tokens:,}", file=sys.stderr)
    if args.stdout:
        print(memo)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantai-credit",
        description="Run an AI distressed-credit committee on any situation file.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run the committee on a situation YAML/JSON file")
    p_run.add_argument("path", help="path to a situation .yaml/.yml/.json file")
    p_run.add_argument(
        "-o",
        "--out-stem",
        help="output filename stem (default: <company>); writes <stem>_memo.md and <stem>.json",
    )
    p_run.add_argument("--stdout", action="store_true", help="also print the memo to stdout")
    p_run.set_defaults(func=cmd_run)

    p_val = sub.add_parser(
        "validate",
        help="free pre-flight: computed cap-structure snapshot + completeness checks (no LLM)",
    )
    p_val.add_argument("path", help="path to a situation .yaml/.yml/.json file")
    p_val.add_argument("--json", action="store_true", help="emit the snapshot as JSON")
    p_val.set_defaults(func=cmd_validate)

    p_new = sub.add_parser("new", help="scaffold a blank situation file from the template")
    p_new.add_argument("path", help="where to write the new situation file")
    p_new.add_argument("-f", "--force", action="store_true", help="overwrite if it exists")
    p_new.set_defaults(func=cmd_new)

    p_list = sub.add_parser("list", help="list bundled example situations")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
