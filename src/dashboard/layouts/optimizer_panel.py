"""Dashboard layout for portfolio optimizer — efficient frontier + allocation pie."""

import dash_bootstrap_components as dbc
from dash import dcc


def optimizer_panel_layout():
    return dbc.Row([
        # Controls
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Portfolio Optimizer"),
                dbc.CardBody([
                    dbc.Label("Tickers (comma-separated)"),
                    dbc.Input(
                        id="opt-tickers",
                        value="AAPL,MSFT,GOOGL,AMZN,SPY",
                        type="text",
                        className="mb-2",
                    ),
                    dbc.Label("Lookback (trading days)"),
                    dbc.Input(id="opt-period", value=252, type="number", className="mb-2"),
                    dbc.Label("Method"),
                    dbc.Select(
                        id="opt-method",
                        options=[
                            {"label": "Max Sharpe", "value": "max_sharpe"},
                            {"label": "Min Volatility", "value": "min_volatility"},
                            {"label": "Hierarchical Risk Parity", "value": "hrp"},
                        ],
                        value="max_sharpe",
                        className="mb-3",
                    ),
                    dbc.Button(
                        "Optimize", id="opt-run-btn",
                        color="primary", className="w-100",
                    ),
                ]),
            ]),
        ], width=4),

        # Results
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Optimal Allocation"),
                dbc.CardBody([
                    dcc.Graph(id="opt-weights-pie", style={"height": "350px"}),
                ]),
            ]),
            dbc.Card([
                dbc.CardHeader("Efficient Frontier"),
                dbc.CardBody([
                    dcc.Graph(id="opt-frontier-chart", style={"height": "350px"}),
                ]),
            ], className="mt-3"),
        ], width=8),
    ])
