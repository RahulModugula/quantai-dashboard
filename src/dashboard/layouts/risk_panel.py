import dash_bootstrap_components as dbc
from dash import dcc, html


def risk_panel_layout() -> html.Div:
    def metric_card(label, id_):
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H6(label, className="text-muted text-center"),
                        html.H4(id=id_, children="—", className="text-center"),
                    ]
                )
            ],
            className="h-100",
        )

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
                                                "Backtest Configuration", className="mb-0 d-inline"
                                            ),
                                            dbc.Badge(
                                                "Educational Only",
                                                color="warning",
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
                                                                id="backtest-ticker",
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
                                                            html.Label("Initial Capital ($)"),
                                                            dbc.Input(
                                                                id="backtest-capital",
                                                                value=100000,
                                                                type="number",
                                                            ),
                                                        ],
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label("Buy Threshold"),
                                                            dbc.Input(
                                                                id="buy-threshold",
                                                                value=0.6,
                                                                type="number",
                                                                step=0.05,
                                                            ),
                                                        ],
                                                        width=3,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(" "),
                                                            dbc.Button(
                                                                "Run Backtest",
                                                                id="run-backtest-btn",
                                                                color="primary",
                                                                className="w-100 d-block mt-4",
                                                            ),
                                                        ],
                                                        width=3,
                                                    ),
                                                ]
                                            ),
                                            html.Div(id="backtest-status", className="mt-2"),
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
                    dbc.Col(metric_card("Sharpe Ratio", "sharpe-val"), width=2),
                    dbc.Col(metric_card("Sortino Ratio", "sortino-val"), width=2),
                    dbc.Col(metric_card("Max Drawdown", "max-dd-val"), width=2),
                    dbc.Col(metric_card("Win Rate", "win-rate-val"), width=2),
                    dbc.Col(metric_card("Total Return", "backtest-return-val"), width=2),
                    dbc.Col(metric_card("Total Trades", "total-trades-val"), width=2),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Equity Curve"),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="backtest-equity-chart",
                                                style={"height": "300px"},
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Drawdown"),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="backtest-drawdown-chart",
                                                style={"height": "300px"},
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=4,
                    ),
                ]
            ),
        ]
    )
