import dash_bootstrap_components as dbc
from dash import dcc, html


def advisor_panel_layout() -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Financial Advisor", className="mb-0 d-inline"),
                        dbc.Badge("Educational Only — Not SEBI Advice", color="danger", className="ms-2"),
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Age"),
                                dbc.Input(id="adv-age", type="number", value=28, min=18, max=80),
                            ], width=2),
                            dbc.Col([
                                html.Label("Investment Horizon (years)"),
                                dbc.Input(id="adv-horizon", type="number", value=15, min=1, max=40),
                            ], width=2),
                            dbc.Col([
                                html.Label("Income Stability (1-5)"),
                                dcc.Slider(id="adv-income", min=1, max=5, step=1, value=3,
                                           marks={i: str(i) for i in range(1, 6)}),
                            ], width=3),
                            dbc.Col([
                                html.Label("Loss Tolerance (1-5)"),
                                dcc.Slider(id="adv-loss", min=1, max=5, step=1, value=3,
                                           marks={i: str(i) for i in range(1, 6)}),
                            ], width=3),
                            dbc.Col([
                                html.Label(" "),
                                dbc.Button("Get Advice", id="adv-submit-btn", color="primary", className="w-100 d-block mt-4"),
                            ], width=2),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Emergency Fund (months)"),
                                dbc.Input(id="adv-emergency", type="number", value=6, min=0, max=24),
                            ], width=3),
                            dbc.Col([
                                html.Label("Debt-to-Income (%)"),
                                dbc.Input(id="adv-debt", type="number", value=20, min=0, max=100),
                            ], width=3),
                        ]),
                    ]),
                ])
            ], width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Risk Profile"),
                    dbc.CardBody([
                        html.Div(id="risk-profile-result"),
                    ]),
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recommended Asset Allocation"),
                    dbc.CardBody([
                        dcc.Graph(id="allocation-pie-chart", style={"height": "300px"}),
                    ]),
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Rebalancing Suggestions"),
                    dbc.CardBody([
                        html.Div(id="rebalancing-suggestions"),
                    ]),
                ])
            ], width=4),
        ]),
    ])
