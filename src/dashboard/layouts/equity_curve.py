import dash_bootstrap_components as dbc
from dash import dcc, html


def equity_curve_layout() -> html.Div:
    return html.Div(
        [
            dbc.Row(
                [
                    # Summary cards
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H6("Portfolio Value", className="text-muted"),
                                        html.H4(id="portfolio-value", children="$0.00"),
                                    ]
                                )
                            ]
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H6("Total Return", className="text-muted"),
                                        html.H4(id="total-return", children="0.00%"),
                                    ]
                                )
                            ]
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H6("Cash", className="text-muted"),
                                        html.H4(id="cash-value", children="$0.00"),
                                    ]
                                )
                            ]
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H6("Open Positions", className="text-muted"),
                                        html.H4(id="open-positions", children="0"),
                                    ]
                                )
                            ]
                        ),
                        width=3,
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
                                    dbc.CardHeader("Portfolio Equity Curve"),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="equity-curve-chart", style={"height": "350px"}
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
                                    dbc.CardHeader("Holdings"),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="holdings-table"),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    ),
                ]
            ),
        ]
    )
