import dash_bootstrap_components as dbc
from dash import dcc, html


def price_chart_layout() -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col(html.H5("Live Price Chart", className="mb-0"), width=8),
                            dbc.Col([
                                dcc.Dropdown(
                                    id="ticker-select",
                                    options=[
                                        {"label": t, "value": t}
                                        for t in ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY"]
                                    ],
                                    value="AAPL",
                                    clearable=False,
                                    style={"minWidth": "120px"},
                                )
                            ], width=4),
                        ])
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="price-chart", style={"height": "400px"}),
                    ]),
                ])
            ], width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Prediction Signal"),
                    dbc.CardBody([
                        html.Div(id="signal-display"),
                    ]),
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Feature Importance"),
                    dbc.CardBody([
                        dcc.Graph(id="feature-importance-chart", style={"height": "200px"}),
                    ]),
                ])
            ], width=8),
        ], className="mb-3"),
    ])
