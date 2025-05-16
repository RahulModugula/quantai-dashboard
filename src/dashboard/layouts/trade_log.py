import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html


def trade_log_layout() -> html.Div:
    return html.Div([
        dbc.Card([
            dbc.CardHeader("Trade Log (Paper Trading)"),
            dbc.CardBody([
                dash_table.DataTable(
                    id="trade-log-table",
                    columns=[
                        {"name": "Date", "id": "date"},
                        {"name": "Ticker", "id": "ticker"},
                        {"name": "Side", "id": "side"},
                        {"name": "Shares", "id": "shares"},
                        {"name": "Price", "id": "price"},
                        {"name": "Commission", "id": "commission"},
                        {"name": "P&L", "id": "pnl"},
                    ],
                    data=[],
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left", "padding": "8px"},
                    style_header={"fontWeight": "bold", "backgroundColor": "#f8f9fa"},
                    style_data_conditional=[
                        {
                            "if": {"filter_query": "{side} = buy"},
                            "color": "#28a745",
                        },
                        {
                            "if": {"filter_query": "{side} = sell"},
                            "color": "#dc3545",
                        },
                        {
                            "if": {"filter_query": "{pnl} > 0"},
                            "fontWeight": "bold",
                        },
                    ],
                    page_size=20,
                    sort_action="native",
                    filter_action="native",
                ),
            ]),
        ]),
    ])
