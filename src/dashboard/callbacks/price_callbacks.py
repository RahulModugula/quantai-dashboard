import httpx
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, html
import dash_bootstrap_components as dbc

BASE_URL = "http://localhost:8000"


def format_signal_badge(signal: str, prob: float, confidence: float) -> list:
    color = {"buy": "success", "sell": "danger", "hold": "secondary"}.get(signal, "secondary")
    return [
        dbc.Badge(signal.upper(), color=color, className="fs-5 me-2"),
        html.Span(f"P(up) = {prob:.1%}", className="text-muted me-3"),
        html.Span(f"Confidence: {confidence:.1%}", className="text-muted"),
    ]


def register_price_callbacks(app):
    @app.callback(
        Output("price-chart", "figure"),
        Output("signal-display", "children"),
        Output("feature-importance-chart", "figure"),
        Input("interval-update", "n_intervals"),
        Input("ticker-select", "value"),
    )
    def update_price_chart(n, ticker):
        from src.data.storage import load_ohlcv

        # Load OHLCV for candlestick
        try:
            df = load_ohlcv(ticker)
            df["date"] = pd.to_datetime(df["date"])
            df = df.tail(120)

            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=df["date"],
                        open=df["open"],
                        high=df["high"],
                        low=df["low"],
                        close=df["close"],
                        name=ticker,
                        increasing_line_color="#28a745",
                        decreasing_line_color="#dc3545",
                    )
                ]
            )
            fig.update_layout(
                title=f"{ticker} — Last 120 Trading Days",
                xaxis_rangeslider_visible=False,
                template="plotly_white",
                margin=dict(l=40, r=20, t=40, b=40),
            )
        except Exception:
            fig = go.Figure()
            fig.add_annotation(text="No price data — run seed_data.py first", showarrow=False)

        # Prediction signal
        signal_children = [html.Span("No model loaded", className="text-muted")]
        feat_fig = go.Figure()

        try:
            resp = httpx.get(f"{BASE_URL}/api/predictions/{ticker}", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                signal_children = format_signal_badge(
                    data.get("signal", "hold"),
                    data.get("probability_up", 0.5),
                    data.get("confidence", 0),
                )

                # Feature importance bar chart
                importances = data.get("feature_importances", {})
                if importances:
                    top = dict(list(importances.items())[:10])
                    feat_fig = go.Figure(
                        go.Bar(
                            x=list(top.values()),
                            y=list(top.keys()),
                            orientation="h",
                            marker_color="#4A90D9",
                        )
                    )
                    feat_fig.update_layout(
                        title="Top Feature Importances",
                        template="plotly_white",
                        margin=dict(l=10, r=10, t=30, b=10),
                        xaxis_title="Importance",
                        yaxis={"autorange": "reversed"},
                    )
        except Exception:
            pass

        return fig, signal_children, feat_fig
