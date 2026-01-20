#!/usr/bin/env python
"""Run model and feature ablation study.

Usage:
    python scripts/run_ablation.py --ticker AAPL
    python scripts/run_ablation.py --ticker AAPL --type feature
    python scripts/run_ablation.py --ticker AAPL --type both --output ablation_report.json
    python scripts/run_ablation.py --ticker AAPL --fast
"""

import argparse
import json
import sys

# Ensure project root is on path when run directly
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _print_model_table(results: dict) -> None:
    members = results["members"]
    sorted_members = sorted(
        members.items(), key=lambda kv: kv[1]["marginal_contribution"], reverse=True
    )
    print(f"\n  Baseline Sharpe: {results['baseline_sharpe']:.4f}")
    print(f"\n  {'Model':<10} {'Sharpe Without':>15} {'Marginal +Sharpe':>18}")
    print("  " + "-" * 45)
    for name, data in sorted_members:
        print(
            f"  {name:<10} {data['sharpe_without']:>15.4f} {data['marginal_contribution']:>+18.4f}"
        )
    print(f"\n  Conclusion: {results['conclusion']}\n")


def _print_feature_table(results: dict) -> None:
    groups = results["groups"]
    sorted_groups = sorted(
        groups.items(), key=lambda kv: kv[1]["marginal_contribution"], reverse=True
    )
    print(f"\n  Baseline Sharpe: {results['baseline_sharpe']:.4f}")
    print(f"\n  {'Group':<15} {'Sharpe Without':>15} {'Marginal +Sharpe':>18}")
    print("  " + "-" * 50)
    for name, data in sorted_groups:
        print(
            f"  {name:<15} {data['sharpe_without']:>15.4f} {data['marginal_contribution']:>+18.4f}"
        )
    print(f"\n  Conclusion: {results['conclusion']}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run model and feature ablation study")
    parser.add_argument("--ticker", default="AAPL", help="Ticker symbol to study (default: AAPL)")
    parser.add_argument(
        "--type",
        choices=["model", "feature", "both"],
        default="model",
        help="Ablation type: model member, feature group, or both (default: model)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to save JSON report (optional)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        default=True,
        help="Use fast mode for feature ablation (zero features, no retraining)",
    )
    parser.add_argument(
        "--no-fast",
        dest="fast",
        action="store_false",
        help="Disable fast mode — retrain for every ablation run (slow)",
    )
    args = parser.parse_args()

    from src.models.ablation import run_feature_ablation, run_model_ablation

    report: dict = {"ticker": args.ticker}

    if args.type in ("model", "both"):
        print(f"\nRunning model ablation for {args.ticker}...")
        model_results = run_model_ablation(args.ticker)
        report["model_ablation"] = model_results
        print("\n=== Model Member Ablation ===")
        _print_model_table(model_results)

    if args.type in ("feature", "both"):
        print(f"\nRunning feature group ablation for {args.ticker} (fast={args.fast})...")
        feature_results = run_feature_ablation(args.ticker, fast_mode=args.fast)
        report["feature_ablation"] = feature_results
        print("\n=== Feature Group Ablation ===")
        _print_feature_table(feature_results)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
