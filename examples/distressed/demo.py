#!/usr/bin/env python3
"""
Demo script for QuantAI Credit Committee.

This script displays the pre-rendered ATI Physical Therapy memo with ANSI colors
in the terminal. It requires no external dependencies beyond the Python stdlib
and no API keys.

Run with: python -m examples.distressed.demo
"""

from pathlib import Path


def print_header():
    """Print the demo header banner with ANSI colors."""
    cyan = "\033[1;36m"
    yellow = "\033[1;33m"
    reset = "\033[0m"
    
    print()
    print(f"{cyan}{'=' * 70}{reset}")
    print(f"{cyan}QuantAI Credit Committee — Live Demo{reset}")
    print(f"{yellow}ATI Physical Therapy | April 2023 TSA Analysis{reset}")
    print(f"{cyan}(No API key required — showing pre-rendered committee output){reset}")
    print(f"{cyan}{'=' * 70}{reset}")
    print()


def print_summary():
    """Print a quick summary of the trade."""
    green = "\033[1;32m"
    cyan = "\033[1;36m"
    yellow = "\033[1;33m"
    reset = "\033[0m"
    
    print(f"{cyan}{'─' * 70}{reset}")
    print(f"{cyan}QUICK SUMMARY{reset}")
    print(f"{cyan}{'─' * 70}{reset}")
    print(f"{green}Trade:{reset} 2L PIK Convertible Notes (April 2023 TSA)")
    print(f"{green}Entry:{reset} 8% PIK, Aug 2028 maturity, fulcrum security")
    print(f"{green}Thesis:{reset} PT wage normalization → EBITDA recovery")
    print(f"{green}Outcome (Aug 2025):{reset} {yellow}$523.3M take-private @ 11.2x EBITDA{reset}")
    print(f"  {green}Base thesis: CONFIRMED{reset} | {green}Bull thesis: CONFIRMED{reset}")
    print()


def print_architecture():
    """Print the agent pipeline architecture as ASCII art."""
    print("Agent Pipeline Architecture:")
    print()
    print("  Phase 1 (parallel):  CapStructureAgent  +  SituationAgent")
    print("                              ↓                      ↓")
    print("  Phase 2:               CreditRiskAgent (stress-tests both briefs)")
    print("                                    ↓")
    print("  Phase 3:           CreditCommitteeAgent → IC Memo")
    print()


def print_memo():
    """Read and print the memo with colored sections."""
    memo_path = Path(__file__).parent / "ati_2023_memo.md"
    
    if not memo_path.exists():
        print(f"Error: Memo file not found at {memo_path}")
        return
    
    with open(memo_path, "r") as f:
        lines = f.readlines()
    
    # ANSI color codes
    bold_cyan = "\033[1;36m"
    bold_green = "\033[1;32m"
    bold_yellow = "\033[1;33m"
    bold_white = "\033[1;37m"
    reset = "\033[0m"
    
    # Lines that should be colored green
    green_prefixes = ["RECOMMENDATION:", "INSTRUMENT:", "SIZING:", "TARGET PRICE:", "CATALYST:"]
    
    # Lines that should be colored yellow
    yellow_prefixes = ["VERDICT:", "RISK RATING:"]
    
    for line in lines:
        stripped = line.rstrip()
        
        # Check for ## headings
        if stripped.startswith("## "):
            print(f"{bold_cyan}{stripped}{reset}")
        # Check for green-colored lines
        elif any(stripped.startswith(prefix) for prefix in green_prefixes):
            print(f"{bold_green}{stripped}{reset}")
        # Check for yellow-colored lines
        elif any(stripped.startswith(prefix) for prefix in yellow_prefixes):
            print(f"{bold_yellow}{stripped}{reset}")
        # Color **bold** text
        else:
            # Replace **text** with colored bold text
            colored_line = stripped.replace("**", f"{bold_white}", 1).replace("**", f"{reset}", 1)
            print(colored_line)


def print_footer():
    """Print the outcome footer."""
    green = "\033[1;32m"
    cyan = "\033[1;36m"
    reset = "\033[0m"
    
    print()
    print(f"{cyan}{'─' * 70}{reset}")
    print(f"{green}Outcome (August 1, 2025): Knighthead/Marathon take-private closed{reset}")
    print(f"{green}at $2.85/share — TEV $523.3M, ~11.2x LTM Adj EBITDA.{reset}")
    print(f"{green}Base thesis CONFIRMED. Bull thesis CONFIRMED.{reset}")
    print(f"{cyan}{'─' * 70}{reset}")
    print()


def print_key_takeaways():
    """Print key takeaways from the analysis."""
    green = "\033[1;32m"
    cyan = "\033[1;36m"
    yellow = "\033[1;33m"
    reset = "\033[0m"
    
    print(f"{cyan}{'─' * 70}{reset}")
    print(f"{cyan}KEY TAKEAWAYS{reset}")
    print(f"{cyan}{'─' * 70}{reset}")
    print(f"{green}✓{reset} 4-agent debate: CapStructure + Situation → CreditRisk → Committee")
    print(f"{green}✓{reset} {yellow}Fulcrum security{reset}: 2L PIK convertible engineered for loan-to-own")
    print(f"{green}✓{reset} {yellow}Supply-side shock{reset}: PT wage inflation, not demand destruction")
    print(f"{green}✓{reset} {yellow}Asymmetric upside{reset}: 250-320c par in bull case")
    print(f"{green}✓{reset} {yellow}Bounded downside{reset}: 55-70c par bear case recovery")
    print(f"{green}✓{reset} {yellow}Thesis validated{reset}: Knighthead/Marathon take-private @ 11.2x EBITDA")
    print(f"{cyan}{'─' * 70}{reset}")
    print()


def main():
    """Main entry point for the demo."""
    print_header()
    print_summary()
    print_architecture()
    print_memo()
    print_footer()
    print_key_takeaways()
    
    print("To generate a live run:")
    print("  export ANTHROPIC_API_KEY=sk-ant-...")
    print("  python -m examples.distressed.ati_2023")
    print()
    print("Full system (equity agents + dashboard + API):")
    print("  docker compose up --build")
    print()


if __name__ == "__main__":
    main()
