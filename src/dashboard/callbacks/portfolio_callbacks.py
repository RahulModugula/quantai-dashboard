import httpx
import plotly.graph_objects as go
from dash import Input, Output, dash_table, html

BASE_URL = "http://localhost:8000"


def fmt_currency(val: float) -> str:
    return f"${val:,.2f}"


def fmt_pct(val: float) -> str:
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.2%}"


def register_portfolio_callbacks(app):
    @app.callback(
        Output("portfolio-value", "children"),
        Output("total-return", "children"),
        Output("cash-value", "children"),
        Output("open-positions", "children"),
        Output("equity-curve-chart", "figure"),
        Output("holdings-table", "children"),
        Input("interval-update", "n_intervals"),
    )
    def update_portfolio(n):
        fig = go.Figure()
        default_val = ("—", "—", "—", "0", fig, html.Div("No data"))

        try:
            resp = httpx.get(f"{BASE_URL}/api/portfolio/", timeout=2)
            if resp.status_code != 200:
                return default_val
            data = resp.json()

            total_val = fmt_currency(data.get("total_value", 0))
            ret = fmt_pct(data.get("cumulative_return", 0))
            cash = fmt_currency(data.get("cash", 0))
            n_pos = str(len(data.get("holdings", [])))

            # Equity curve
            hist_resp = httpx.get(f"{BASE_URL}/api/portfolio/history", timeout=2)
            if hist_resp.status_code == 200:
                snaps = hist_resp.json().get("snapshots", [])
                if snaps:
                    dates = [s["timestamp"] for s in snaps]
                    values = [s["total_value"] for s in snaps]
                    fig.add_trace(go.Scatter(x=dates, y=values, mode="lines", name="Portfolio Value",
                                            line=dict(color="#4A90D9", width=2)))
                    fig.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=20, b=40),
                                      yaxis_title="Value ($)")

            # Holdings table
            holdings = data.get("holdings", [])
            if holdings:
                table = dash_table.DataTable(
                    columns=[
                        {"name": "Ticker", "id": "ticker"},
                        {"name": "Shares", "id": "shares"},
                        {"name": "Avg Price", "id": "avg_price"},
                        {"name": "Current Value", "id": "current_value"},
                        {"name": "Unrealized P&L", "id": "unrealized_pnl"},
                    ],
                    data=[{**h, "avg_price": f"${h['avg_price']:.2f}",
                            "current_value": f"${h['current_value']:.2f}",
                            "unrealized_pnl": f"${h['unrealized_pnl']:.2f}"} for h in holdings],
                    style_cell={"textAlign": "left"},
                )
            else:
                table = html.Div("No open positions", className="text-muted")

            return total_val, ret, cash, n_pos, fig, table
        except Exception:
            return default_val
