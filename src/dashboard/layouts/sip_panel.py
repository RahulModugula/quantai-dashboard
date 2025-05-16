import dash_bootstrap_components as dbc
from dash import dcc, html


def sip_panel_layout() -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("SIP Calculator", className="mb-0 d-inline"),
                        dbc.Badge("Not Financial Advice", color="warning", className="ms-2"),
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Monthly SIP (₹)"),
                                dbc.Input(id="sip-amount", type="number", value=10000, step=500),
                            ], width=4),
                            dbc.Col([
                                html.Label("Duration (years)"),
                                dbc.Input(id="sip-duration", type="number", value=20, min=1, max=40),
                            ], width=4),
                            dbc.Col([
                                html.Label("Expected Return (%)"),
                                dbc.Input(id="sip-return", type="number", value=12, step=0.5),
                            ], width=4),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Inflation Rate (%)"),
                                dbc.Input(id="sip-inflation", type="number", value=6, step=0.5),
                            ], width=3),
                            dbc.Col([
                                html.Label("Tax Rate on Gains (%)"),
                                dbc.Input(id="sip-tax", type="number", value=10, step=1),
                            ], width=3),
                            dbc.Col([
                                html.Label("Annual Step-Up (%)"),
                                dbc.Input(id="sip-stepup", type="number", value=10, step=5),
                            ], width=3),
                            dbc.Col([
                                html.Label(" "),
                                dbc.Button("Calculate", id="sip-calc-btn", color="success", className="w-100 d-block mt-4"),
                            ], width=3),
                        ]),
                    ]),
                ])
            ], width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("Total Invested", className="text-muted"),
                    html.H4(id="sip-invested", children="—"),
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("Pre-Tax Corpus", className="text-muted"),
                    html.H4(id="sip-pretax", children="—"),
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("Post-Tax Corpus", className="text-muted"),
                    html.H4(id="sip-posttax", children="—"),
                ])
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("Real Value (Inflation-Adj.)", className="text-muted"),
                    html.H4(id="sip-real", children="—"),
                ])
            ]), width=3),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Wealth Growth Over Time"),
                    dbc.CardBody([
                        dcc.Graph(id="sip-growth-chart", style={"height": "350px"}),
                    ]),
                ])
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Summary"),
                    dbc.CardBody([
                        html.Div(id="sip-summary"),
                    ]),
                ])
            ], width=4),
        ]),
    ])
