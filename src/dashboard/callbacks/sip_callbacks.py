import httpx
import plotly.graph_objects as go
from dash import Input, Output, State, html

BASE_URL = "http://localhost:8000"


def fmt_inr(val: float) -> str:
    """Format large numbers in Indian numbering system (lakhs/crores)."""
    if val >= 1e7:
        return f"₹{val / 1e7:.2f} Cr"
    elif val >= 1e5:
        return f"₹{val / 1e5:.2f} L"
    return f"₹{val:,.0f}"


def register_sip_callbacks(app):
    @app.callback(
        Output("sip-invested", "children"),
        Output("sip-pretax", "children"),
        Output("sip-posttax", "children"),
        Output("sip-real", "children"),
        Output("sip-growth-chart", "figure"),
        Output("sip-summary", "children"),
        Input("sip-calc-btn", "n_clicks"),
        State("sip-amount", "value"),
        State("sip-duration", "value"),
        State("sip-return", "value"),
        State("sip-inflation", "value"),
        State("sip-tax", "value"),
        State("sip-stepup", "value"),
        prevent_initial_call=True,
    )
    def calculate_sip(n_clicks, amount, duration, ret, inflation, tax, stepup):
        try:
            resp = httpx.post(f"{BASE_URL}/api/sip/calculate", json={
                "monthly_amount": amount or 10000,
                "duration_years": duration or 20,
                "expected_return": (ret or 12) / 100,
                "inflation_rate": (inflation or 6) / 100,
                "tax_rate": (tax or 10) / 100,
                "step_up_pct": (stepup or 0) / 100,
            }, timeout=5)

            if resp.status_code != 200:
                return "—", "—", "—", "—", go.Figure(), html.Div("Error")

            data = resp.json()
            breakdown = data.get("year_breakdown", [])

            invested = fmt_inr(data["total_invested"])
            pretax = fmt_inr(data["pre_tax_corpus"])
            posttax = fmt_inr(data["post_tax_corpus"])
            real = fmt_inr(data["inflation_adjusted_value"])

            # Growth chart
            fig = go.Figure()
            if breakdown:
                years = [b["year"] for b in breakdown]
                fig.add_trace(go.Scatter(x=years, y=[b["total_invested"] for b in breakdown],
                                         name="Total Invested", fill="tozeroy",
                                         line=dict(color="#adb5bd", width=1)))
                fig.add_trace(go.Scatter(x=years, y=[b["pre_tax_corpus"] for b in breakdown],
                                         name="Pre-Tax Corpus", line=dict(color="#4A90D9", width=2)))
                fig.add_trace(go.Scatter(x=years, y=[b["post_tax_corpus"] for b in breakdown],
                                         name="Post-Tax Corpus", line=dict(color="#28a745", width=2)))
                fig.add_trace(go.Scatter(x=years, y=[b["inflation_adjusted"] for b in breakdown],
                                         name="Real Value", line=dict(color="#fd7e14", width=2, dash="dot")))
                fig.update_layout(
                    template="plotly_white",
                    xaxis_title="Year",
                    yaxis_title="Value (₹)",
                    margin=dict(l=40, r=20, t=20, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )

            summary = html.Div([
                html.P([html.Strong("Wealth Gain: "), fmt_inr(data["wealth_gain"])]),
                html.P([html.Strong("Gain %: "), f"{data['wealth_gain_pct']:.1f}%"]),
                html.P([html.Strong("Effective Return (post-tax): "), f"{data['effective_return_post_tax']:.2f}%"]),
                html.P([html.Strong("Tax Paid: "), fmt_inr(data["tax_amount"])]),
                html.Hr(),
                html.Small(data.get("disclaimer", ""), className="text-muted"),
            ])

            return invested, pretax, posttax, real, fig, summary

        except Exception as e:
            return "—", "—", "—", "—", go.Figure(), html.Div(f"Error: {e}", className="text-danger")
