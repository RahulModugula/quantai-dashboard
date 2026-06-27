"""``quantai-credit`` — run an AI distressed-credit committee on any situation.

The credit committee (CapStructure + Situation -> CreditRisk -> Committee) is
data-agnostic: point it at a YAML/JSON file describing *any* distressed company
and it writes an IC-style vote memo.

    quantai-credit new my_deal.yaml      # scaffold a blank situation file
    quantai-credit run my_deal.yaml      # run the committee, write a memo
    quantai-credit list                  # show bundled example situations

`run` needs an LLM API key (any LiteLLM-supported provider). Set one of
ANTHROPIC_API_KEY / OPENAI_API_KEY / OPENROUTER_API_KEY, and optionally
QUANTAI_AGENT_MODEL to pick the model. No key? Try the zero-setup demo first:

    python -m examples.distressed.demo
"""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

from examples.distressed.models import Situation

SITUATIONS_DIR = Path(__file__).resolve().parent / "situations"
TEMPLATE_PATH = SITUATIONS_DIR / "TEMPLATE.yaml"

_KEY_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
)


def _has_api_key() -> bool:
    # Ollama runs locally with no key; treat an Ollama model as "keyed".
    model = os.environ.get("QUANTAI_AGENT_MODEL", "")
    if model.startswith("ollama/"):
        return True
    return any(os.environ.get(v) for v in _KEY_ENV_VARS)


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_") or "memo"


def cmd_new(args: argparse.Namespace) -> int:
    dest = Path(args.path)
    if dest.exists() and not args.force:
        print(f"refusing to overwrite existing file: {dest} (use --force)", file=sys.stderr)
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE_PATH, dest)
    print(f"Wrote situation template to {dest}")
    print("Edit it, then run:  quantai-credit run", dest)
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
        except Exception as exc:  # noqa: BLE001 - listing must never hard-fail
            label = f"(could not parse: {exc})"
        print(f"  {p.relative_to(SITUATIONS_DIR.parent.parent)}")
        print(f"      {label}\n")
    print("Run one with:  quantai-credit run <path>")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        situation = Situation.from_file(args.path)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        print(f"Could not load situation: {exc}", file=sys.stderr)
        return 1

    if not _has_api_key():
        print(
            "No LLM API key found. The committee calls an LLM to write the memo.\n"
            "Set one of: " + ", ".join(_KEY_ENV_VARS) + "\n"
            "  (or QUANTAI_AGENT_MODEL=ollama/llama3 to run locally with no key)\n\n"
            "To see a full sample memo with zero setup, run:\n"
            "  python -m examples.distressed.demo",
            file=sys.stderr,
        )
        return 2

    # Imported lazily so `new`/`list` work without litellm or a network stack.
    from examples.distressed.agents import run_credit_committee

    print(f"Running 4-agent credit committee on {situation.company} ...", file=sys.stderr)
    result = asyncio.run(run_credit_committee(situation))

    memo = result.rendered_memo()
    out_path = Path(args.out) if args.out else Path(f"{_slug(situation.company)}_memo.md")
    out_path.write_text(memo)
    print(f"\nMemo written to {out_path}", file=sys.stderr)
    print(f"Total LLM tokens used: {result.total_tokens:,}", file=sys.stderr)
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
    p_run.add_argument("-o", "--out", help="output memo path (default: <company>_memo.md)")
    p_run.add_argument("--stdout", action="store_true", help="also print the memo to stdout")
    p_run.set_defaults(func=cmd_run)

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
