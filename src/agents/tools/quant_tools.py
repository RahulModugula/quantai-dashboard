"""Quantitative tools — wraps existing ML predictions, SHAP, and signals."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# LiteLLM-format tool schemas
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_ml_prediction",
            "description": (
                "Get the ML ensemble model's next-day directional prediction for a ticker. "
                "Returns probability of up move and raw signal."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. AAPL",
                    }
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_shap_importance",
            "description": (
                "Get SHAP feature importance for the trained ensemble model on a ticker. "
                "Returns top features driving the prediction with their relative importance scores."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. AAPL",
                    }
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_technical_signals",
            "description": (
                "Get the latest technical indicator values for a ticker including RSI, MACD, "
                "Bollinger Bands, ATR, and momentum. Returns current values and their interpretation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. AAPL",
                    }
                },
                "required": ["ticker"],
            },
        },
    },
]


def get_ml_prediction(ticker: str) -> dict[str, Any]:
    """Return ML ensemble prediction for the ticker."""
    ticker = ticker.upper()
    try:
        from src.api.dependencies import get_model_bundle
        from src.data.storage import load_features

        bundle, meta = get_model_bundle()
        if bundle is None:
            return {"error": "No trained model available", "ticker": ticker}

        df = load_features(ticker)
        if df is None or df.empty:
            return {"error": f"No feature data for {ticker}", "ticker": ticker}

        model = bundle["model"]
        scaler = bundle["scaler"]
        feature_names = meta.get("feature_names", [])

        cols = (
            feature_names
            if feature_names
            else [c for c in df.columns if c not in ("id", "date", "ticker", "target")]
        )
        X = df[cols].dropna().tail(1)
        if X.empty:
            return {"error": "Insufficient feature data", "ticker": ticker}

        X_scaled = scaler.transform(X.values)
        prob = float(model.predict_proba(X_scaled)[0][1])
        from src.config import settings

        signal = (
            "BUY"
            if prob >= settings.buy_threshold
            else ("SELL" if prob <= settings.sell_threshold else "HOLD")
        )
        return {
            "ticker": ticker,
            "probability_up": round(prob, 4),
            "signal": signal,
            "buy_threshold": settings.buy_threshold,
            "sell_threshold": settings.sell_threshold,
        }
    except Exception as exc:
        logger.warning(f"ML prediction failed for {ticker}: {exc}")
        return {"error": str(exc), "ticker": ticker}


def get_shap_importance(ticker: str) -> dict[str, Any]:
    """Return top SHAP features for the ticker."""
    ticker = ticker.upper()
    try:
        from src.api.dependencies import get_model_bundle
        from src.data.storage import load_features
        from src.models.shap_analysis import compute_shap_importance

        bundle, meta = get_model_bundle()
        if bundle is None:
            return {"error": "No trained model available", "ticker": ticker}

        df = load_features(ticker)
        if df is None or df.empty:
            return {"error": f"No feature data for {ticker}", "ticker": ticker}

        model = bundle["model"]
        scaler = bundle["scaler"]
        feature_names = meta.get("feature_names", [])
        cols = (
            feature_names
            if feature_names
            else [c for c in df.columns if c not in ("id", "date", "ticker", "target")]
        )
        X = df[cols].dropna().tail(200)
        X_scaled = scaler.transform(X.values)

        result = compute_shap_importance(model, X_scaled, feature_names=cols, max_samples=100)
        mean_abs = result.get("mean_abs_shap", {})
        sorted_features = sorted(mean_abs.items(), key=lambda x: x[1], reverse=True)
        total = sum(v for _, v in sorted_features) or 1.0
        top10 = [{"feature": k, "importance": round(v / total, 4)} for k, v in sorted_features[:10]]
        return {"ticker": ticker, "top_features": top10}
    except Exception as exc:
        logger.warning(f"SHAP importance failed for {ticker}: {exc}")
        return {"error": str(exc), "ticker": ticker}


def get_technical_signals(ticker: str) -> dict[str, Any]:
    """Return latest technical indicator snapshot for the ticker."""
    ticker = ticker.upper()
    try:
        from src.data.storage import load_features

        df = load_features(ticker)
        if df is None or df.empty:
            return {"error": f"No feature data for {ticker}", "ticker": ticker}

        row = df.sort_values("date").iloc[-1]

        def _f(col: str, decimals: int = 2):
            val = row.get(col)
            if val is None:
                return None
            try:
                return round(float(val), decimals)
            except (TypeError, ValueError):
                return None

        rsi = _f("rsi_14")
        macd = _f("macd", 4)
        macd_signal = _f("macd_signal", 4)
        bb_pct = _f("bb_pct_b", 4)
        atr = _f("atr_14", 4)
        adx = _f("adx_14")
        momentum_5 = _f("momentum_5", 4)
        momentum_20 = _f("momentum_20", 4)
        vol_ratio = _f("volume_ratio")

        interpretations = []
        if rsi is not None:
            if rsi > 70:
                interpretations.append(f"RSI {rsi} — overbought territory")
            elif rsi < 30:
                interpretations.append(f"RSI {rsi} — oversold territory")
            else:
                interpretations.append(f"RSI {rsi} — neutral")
        if macd is not None and macd_signal is not None:
            cross = "bullish" if macd > macd_signal else "bearish"
            interpretations.append(f"MACD {cross} crossover (MACD={macd}, signal={macd_signal})")
        if bb_pct is not None:
            if bb_pct > 1.0:
                interpretations.append("Price above upper Bollinger Band — extended")
            elif bb_pct < 0.0:
                interpretations.append("Price below lower Bollinger Band — compressed")
        if momentum_20 is not None:
            direction = "positive" if momentum_20 > 0 else "negative"
            interpretations.append(f"20-day momentum is {direction} ({momentum_20:.2%})")

        return {
            "ticker": ticker,
            "date": str(row.get("date", "")),
            "indicators": {
                "rsi_14": rsi,
                "macd": macd,
                "macd_signal": macd_signal,
                "bb_pct_b": bb_pct,
                "atr_14": atr,
                "adx_14": adx,
                "momentum_5": momentum_5,
                "momentum_20": momentum_20,
                "volume_ratio": vol_ratio,
            },
            "interpretations": interpretations,
        }
    except Exception as exc:
        logger.warning(f"Technical signals failed for {ticker}: {exc}")
        return {"error": str(exc), "ticker": ticker}


def dispatch(tool_name: str, args: dict) -> dict:
    """Route a tool call by name to the correct function."""
    if tool_name == "get_ml_prediction":
        return get_ml_prediction(args.get("ticker", ""))
    if tool_name == "get_shap_importance":
        return get_shap_importance(args.get("ticker", ""))
    if tool_name == "get_technical_signals":
        return get_technical_signals(args.get("ticker", ""))
    return {"error": f"Unknown tool: {tool_name}"}
