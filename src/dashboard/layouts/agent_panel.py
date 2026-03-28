"""AI Reasoning tab layout — shows multi-agent debate and final decision."""

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.config import settings

_TICKERS = settings.tickers

# Color scheme per agent
_AGENT_COLORS = {
    "quant": "#4A90D9",       # blue
    "news": "#27AE60",        # green
    "risk": "#E74C3C",        # red
    "portfolio_manager": "#8E44AD",  # purple
}

_AGENT_ICONS = {
    "quant": "Q",
    "news": "N",
    "risk": "R",
    "portfolio_manager": "PM",
}

_AGENT_LABELS = {
    "quant": "QuantAgent",
    "news": "NewsAgent",
    "risk": "RiskAgent",
    "portfolio_manager": "PortfolioManagerAgent",
}


def _agent_card(agent_key: str, content_id: str) -> dbc.Card:
    color = _AGENT_COLORS[agent_key]
    icon = _AGENT_ICONS[agent_key]
    label = _AGENT_LABELS[agent_key]
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.Span(
                                icon,
                                style={
                                    "display": "inline-block",
                                    "width": "32px",
                                    "height": "32px",
                                    "lineHeight": "32px",
                                    "textAlign": "center",
                                    "borderRadius": "50%",
                                    "backgroundColor": color,
                                    "color": "white",
                                    "fontWeight": "bold",
                                    "fontSize": "12px",
                                    "marginRight": "10px",
                                },
                            ),
                            width="auto",
                        ),
                        dbc.Col(html.Strong(label, style={"color": color})),
                    ],
                    align="center",
                )
            ),
            dbc.CardBody(
                html.Div(
                    id=content_id,
                    style={"whiteSpace": "pre-wrap", "fontSize": "13px", "minHeight": "80px"},
                    children=html.Span("Awaiting analysis...", className="text-muted"),
                )
            ),
        ],
        className="mb-3",
        style={"borderLeft": f"4px solid {color}"},
    )


def agent_panel_layout() -> html.Div:
    return html.Div(
        [
            # Stores
            dcc.Store(id="agent-analysis-id", data=None),
            dcc.Store(id="agent-poll-active", data=False),
            dcc.Interval(id="agent-poll-interval", interval=2000, n_intervals=0, disabled=True),

            # Controls
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5("AI Reasoning", className="mb-0 d-inline"),
                                            dbc.Badge("Multi-Agent", color="primary", className="ms-2"),
                                            dbc.Badge("LiteLLM", color="secondary", className="ms-1"),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Label("Ticker"),
                                                        dcc.Dropdown(
                                                            id="agent-ticker-select",
                                                            options=[
                                                                {"label": t, "value": t}
                                                                for t in _TICKERS
                                                            ],
                                                            value=_TICKERS[0] if _TICKERS else "AAPL",
                                                            clearable=False,
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.Label(" "),
                                                        dbc.Button(
                                                            "Analyze Now",
                                                            id="agent-analyze-btn",
                                                            color="primary",
                                                            className="w-100 d-block mt-4",
                                                        ),
                                                    ],
                                                    width=2,
                                                ),
                                                dbc.Col(
                                                    [html.Div(id="agent-status-msg", className="mt-4")],
                                                    width=7,
                                                ),
                                            ]
                                        )
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    )
                ],
                className="mb-3",
            ),

            # Decision summary card
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.H6("Final Decision", className="mb-0")),
                                    dbc.CardBody(
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(id="agent-decision-badge"),
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.Small("Confidence", className="text-muted d-block"),
                                                        dbc.Progress(
                                                            id="agent-confidence-bar",
                                                            value=0,
                                                            label="",
                                                            style={"height": "20px"},
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        id="agent-reasoning-summary",
                                                        className="text-muted",
                                                        style={"fontSize": "13px"},
                                                    ),
                                                    width=6,
                                                ),
                                            ],
                                            align="center",
                                        )
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    )
                ],
                className="mb-3",
            ),

            # Agent debate cards
            dbc.Row(
                [
                    dbc.Col(_agent_card("quant", "agent-quant-content"), width=6),
                    dbc.Col(_agent_card("news", "agent-news-content"), width=6),
                ],
                className="mb-2",
            ),
            dbc.Row(
                [
                    dbc.Col(_agent_card("risk", "agent-risk-content"), width=6),
                    dbc.Col(_agent_card("portfolio_manager", "agent-pm-content"), width=6),
                ],
                className="mb-2",
            ),

            # Historical accuracy
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Decision History & Accuracy"),
                                dbc.CardBody(dcc.Graph(id="agent-accuracy-chart", style={"height": "250px"})),
                            ]
                        ),
                        width=12,
                    )
                ]
            ),
        ]
    )
