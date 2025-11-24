import httpx
import plotly.graph_objects as go
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc

BASE_URL = "http://localhost:8000"


def register_advisor_callbacks(app):
    @app.callback(
        Output("risk-profile-result", "children"),
        Output("allocation-pie-chart", "figure"),
        Output("rebalancing-suggestions", "children"),
        Input("adv-submit-btn", "n_clicks"),
        State("adv-age", "value"),
        State("adv-horizon", "value"),
        State("adv-income", "value"),
        State("adv-loss", "value"),
        State("adv-emergency", "value"),
        State("adv-debt", "value"),
        prevent_initial_call=True,
    )
    def get_advice(n_clicks, age, horizon, income, loss_tol, emergency, debt):
        try:
            resp = httpx.post(
                f"{BASE_URL}/api/advisor/risk-profile",
                json={
                    "age": age or 30,
                    "investment_horizon_years": horizon or 10,
                    "income_stability": income or 3,
                    "loss_tolerance": loss_tol or 3,
                    "existing_savings_months": emergency or 6,
                    "debt_to_income_pct": (debt or 20) / 100,
                },
                timeout=5,
            )

            if resp.status_code != 200:
                return html.Div("Error fetching advice"), go.Figure(), html.Div()

            data = resp.json()
            profile = data["risk_profile"]
            allocation = data["allocation"]

            color_map = {
                "Conservative": "info",
                "Moderate": "primary",
                "Aggressive": "warning",
                "Very Aggressive": "danger",
            }
            badge_color = color_map.get(profile["category"], "secondary")

            profile_card = html.Div(
                [
                    dbc.Badge(profile["category"], color=badge_color, className="fs-5 mb-2"),
                    html.P(f"Risk Score: {profile['score']}/100", className="fw-bold"),
                    html.P(profile["description"], className="text-muted small"),
                    html.Hr(),
                    html.Small(data.get("disclaimer", ""), className="text-muted"),
                ]
            )

            # Allocation pie
            allocs = allocation["allocations"]
            fig = go.Figure(
                go.Pie(
                    labels=list(allocs.keys()),
                    values=list(allocs.values()),
                    hole=0.4,
                    textinfo="label+percent",
                    textfont_size=11,
                )
            )
            fig.update_layout(
                template="plotly_white",
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
            )

            # Rebalancing (use a dummy current allocation for demo)
            from src.advisor.recommendations import generate_recommendations
            from src.advisor.risk_profile import RiskProfile as RP

            rp = RP(
                score=profile["score"],
                category=profile["category"],
                description=profile["description"],
            )
            # Demo: assume current portfolio is 100% large cap
            current = {"Large Cap Equity": 100}
            recs = generate_recommendations(rp, current)

            rec_rows = []
            for r in recs[:6]:
                color = (
                    "success"
                    if r["action"] == "increase"
                    else "danger"
                    if r["action"] == "reduce"
                    else "secondary"
                )
                rec_rows.append(
                    html.Tr(
                        [
                            html.Td(r["asset_class"]),
                            html.Td(f"{r['current_pct']}%"),
                            html.Td(f"{r['target_pct']}%"),
                            html.Td(
                                dbc.Badge(r["action"], color=color, className="text-uppercase")
                            ),
                        ]
                    )
                )

            rec_table = dbc.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("Asset"),
                                html.Th("Current"),
                                html.Th("Target"),
                                html.Th("Action"),
                            ]
                        )
                    ),
                    html.Tbody(rec_rows),
                ],
                bordered=True,
                hover=True,
                size="sm",
            )

            return profile_card, fig, rec_table

        except Exception as e:
            return html.Div(f"Error: {e}", className="text-danger"), go.Figure(), html.Div()
