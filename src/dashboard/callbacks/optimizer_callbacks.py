"""Callbacks for the portfolio optimizer panel."""

import httpx
import plotly.graph_objects as go
from dash import Input, Output, State


def register_optimizer_callbacks(app):
    @app.callback(
        Output("opt-weights-pie", "figure"),
        Output("opt-frontier-chart", "figure"),
        Input("opt-run-btn", "n_clicks"),
        State("opt-tickers", "value"),
        State("opt-period", "value"),
        State("opt-method", "value"),
        prevent_initial_call=True,
    )
    def run_optimization(n_clicks, tickers_str, period, method):
        tickers = [t.strip() for t in tickers_str.split(",") if t.strip()]
        empty_fig = go.Figure()
        empty_fig.update_layout(template="plotly_white")

        if len(tickers) < 2:
            return empty_fig, empty_fig

        # Get optimized weights
        try:
            resp = httpx.post(
                "http://localhost:8000/api/optimizer/portfolio",
                json={"tickers": tickers, "period": period, "method": method},
                timeout=30,
            )
            weights = resp.json().get("weights", {})
        except Exception:
            return empty_fig, empty_fig

        # Pie chart
        pie = go.Figure(data=[go.Pie(
            labels=list(weights.keys()),
            values=list(weights.values()),
            hole=0.4,
            textinfo="label+percent",
        )])
        pie.update_layout(
            template="plotly_white",
            title=f"{method.replace('_', ' ').title()} Allocation",
            margin=dict(t=40, b=20, l=20, r=20),
        )

        # Efficient frontier
        frontier_fig = go.Figure()
        try:
            resp = httpx.post(
                "http://localhost:8000/api/optimizer/frontier",
                json={"tickers": tickers, "period": period},
                timeout=30,
            )
            data = resp.json()
            frontier = data.get("frontier", [])
            if frontier:
                frontier_fig.add_trace(go.Scatter(
                    x=[p["risk"] for p in frontier],
                    y=[p["return"] for p in frontier],
                    mode="lines",
                    name="Efficient Frontier",
                    line=dict(color="#2c7be5", width=2),
                ))
        except Exception:
            pass

        frontier_fig.update_layout(
            template="plotly_white",
            title="Efficient Frontier",
            xaxis_title="Annualized Risk (σ)",
            yaxis_title="Annualized Return",
            margin=dict(t=40, b=40, l=40, r=20),
        )

        return pie, frontier_fig
