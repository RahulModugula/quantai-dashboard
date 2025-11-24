import httpx
import plotly.graph_objects as go
from dash import Input, Output, State, no_update
import dash_bootstrap_components as dbc

BASE_URL = "http://localhost:8000"
_last_key = {}


def register_backtest_callbacks(app):
    @app.callback(
        Output("backtest-status", "children"),
        Input("run-backtest-btn", "n_clicks"),
        State("backtest-ticker", "value"),
        State("backtest-capital", "value"),
        State("buy-threshold", "value"),
        prevent_initial_call=True,
    )
    def trigger_backtest(n_clicks, ticker, capital, buy_threshold):
        try:
            resp = httpx.post(
                f"{BASE_URL}/api/backtest/run",
                json={
                    "ticker": ticker,
                    "initial_capital": capital or 100000,
                    "buy_threshold": buy_threshold or 0.6,
                    "sell_threshold": 1 - (buy_threshold or 0.6),
                },
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                _last_key["key"] = data.get("key")
                return dbc.Alert(
                    f"Backtest started for {ticker}. Results will appear below.", color="info"
                )
        except Exception as e:
            return dbc.Alert(f"Error: {e}", color="danger")
        return no_update

    @app.callback(
        Output("sharpe-val", "children"),
        Output("sortino-val", "children"),
        Output("max-dd-val", "children"),
        Output("win-rate-val", "children"),
        Output("backtest-return-val", "children"),
        Output("total-trades-val", "children"),
        Output("backtest-equity-chart", "figure"),
        Output("backtest-drawdown-chart", "figure"),
        Input("interval-update", "n_intervals"),
    )
    def update_backtest_results(n):
        empty = ("—", "—", "—", "—", "—", "—", go.Figure(), go.Figure())
        key = _last_key.get("key")
        if not key:
            return empty

        try:
            resp = httpx.get(f"{BASE_URL}/api/backtest/result/{key}", timeout=2)
            if resp.status_code != 200:
                return empty
            data = resp.json()

            if data.get("status") != "complete":
                return empty

            result = data.get("result", {})
            m = result.get("metrics", {})

            sharpe = f"{m.get('sharpe_ratio', 0):.2f}"
            sortino = f"{m.get('sortino_ratio', 0):.2f}"
            mdd = f"{m.get('max_drawdown', 0):.2%}"
            wr = f"{m.get('win_rate', 0):.2%}"
            ret = f"{m.get('total_return', 0):.2%}"
            trades = str(m.get("total_trades", 0))

            equity_data = result.get("equity_curve", [])
            dd_data = result.get("drawdown_series", [])

            eq_fig = go.Figure()
            if equity_data:
                eq_fig.add_trace(
                    go.Scatter(
                        x=[d["date"] for d in equity_data],
                        y=[d["value"] for d in equity_data],
                        mode="lines",
                        name="Backtest Equity",
                        line=dict(color="#4A90D9"),
                    )
                )
                eq_fig.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=20, b=40))

            dd_fig = go.Figure()
            if dd_data:
                dd_fig.add_trace(
                    go.Scatter(
                        x=[d["date"] for d in dd_data],
                        y=[d["drawdown"] * 100 for d in dd_data],
                        fill="tozeroy",
                        mode="lines",
                        name="Drawdown %",
                        line=dict(color="#dc3545"),
                    )
                )
                dd_fig.update_layout(
                    template="plotly_white",
                    margin=dict(l=40, r=20, t=20, b=40),
                    yaxis_title="Drawdown (%)",
                )

            return sharpe, sortino, mdd, wr, ret, trades, eq_fig, dd_fig
        except Exception:
            return empty
