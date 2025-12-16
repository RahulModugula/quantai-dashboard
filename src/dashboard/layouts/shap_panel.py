import dash_bootstrap_components as dbc
from dash import dcc, html


def shap_panel_layout() -> html.Div:
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                "SHAP Feature Importance",
                                                className="mb-0 d-inline",
                                            ),
                                            dbc.Badge(
                                                "Explainability",
                                                color="info",
                                                className="ms-2",
                                            ),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label("Ticker"),
                                                            dcc.Dropdown(
                                                                id="shap-ticker-select",
                                                                options=[
                                                                    {"label": t, "value": t}
                                                                    for t in [
                                                                        "AAPL",
                                                                        "MSFT",
                                                                        "GOOGL",
                                                                        "AMZN",
                                                                        "SPY",
                                                                    ]
                                                                ],
                                                                value="AAPL",
                                                                clearable=False,
                                                            ),
                                                        ],
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(" "),
                                                            dbc.Button(
                                                                "Refresh",
                                                                id="shap-refresh-btn",
                                                                color="primary",
                                                                className="w-100 d-block mt-4",
                                                            ),
                                                        ],
                                                        width=2,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Div(
                                                                id="shap-status",
                                                                className="mt-4",
                                                            )
                                                        ],
                                                        width=7,
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Top 15 Features by Mean |SHAP|"),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="shap-bar-chart",
                                                style={"height": "420px"},
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Per-Model SHAP Breakdown (Top 10)"),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="shap-model-chart",
                                                style={"height": "420px"},
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                ]
            ),
        ]
    )
