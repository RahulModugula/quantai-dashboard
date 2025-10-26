"""Example: Using QuantAI API for analysis and trading signals."""
import requests
import json

BASE_URL = "http://localhost:8000/api"


def main():
    print("QuantAI API Usage Examples\n" + "="*50)

    # 1. Get system status
    print("\n1. Check data availability:")
    resp = requests.get(f"{BASE_URL}/status/data")
    data = resp.json()
    for ticker, info in data["tickers"].items():
        status = "✓" if info.get("available") else "✗"
        print(f"  {status} {ticker}: {info.get('row_count', 0)} rows")

    # 2. Get predictions
    print("\n2. Get predictions for configured tickers:")
    resp = requests.post(f"{BASE_URL}/predictions/batch", json=["AAPL", "MSFT", "GOOGL"])
    preds = resp.json()
    print(f"  Success: {preds['success_count']}, Errors: {preds['error_count']}")
    for pred in preds["predictions"][:3]:
        print(f"  {pred['ticker']}: {pred['signal']} (prob={pred['probability_up']:.2%})")

    # 3. Portfolio status
    print("\n3. Portfolio status:")
    resp = requests.get(f"{BASE_URL}/portfolio/")
    port = resp.json()
    print(f"  Total value: ${port['total_value']:,.2f}")
    print(f"  Cash: ${port['cash']:,.2f}")
    print(f"  Cumulative return: {port['cumulative_return']:.2%}")

    # 4. Risk warnings
    print("\n4. Portfolio risk warnings:")
    resp = requests.get(f"{BASE_URL}/portfolio/warnings")
    warns = resp.json()
    if warns["has_warnings"]:
        for category, items in warns["warnings"].items():
            if items:
                print(f"  {category.upper()}:")
                for item in items:
                    print(f"    - {item}")
    else:
        print("  No warnings - portfolio looks healthy!")

    # 5. Diagnostics
    print("\n5. Model diagnostics:")
    resp = requests.get(f"{BASE_URL}/diagnostics/model-features")
    if resp.status_code == 200:
        diag = resp.json()
        print(f"  Features: {diag['feature_count']}")
        print(f"  Top 3 important:")
        for feat, imp in list(diag["feature_importances"].items())[:3]:
            print(f"    {feat}: {imp:.4f}")

    # 6. Validate configuration
    print("\n6. Configuration validation:")
    resp = requests.post(f"{BASE_URL}/diagnostics/validate-config")
    config = resp.json()
    if config["valid"]:
        print("  ✓ Config is valid")
    else:
        print("  ✗ Errors:")
        for err in config["errors"]:
            print(f"    - {err}")
    if config["warnings"]:
        print("  ⚠ Warnings:")
        for warn in config["warnings"]:
            print(f"    - {warn}")

    print("\n" + "="*50)
    print("For more endpoints, visit http://localhost:8000/api/docs")


if __name__ == "__main__":
    main()
