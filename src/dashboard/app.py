"""
QuantAI Dashboard - Plotly Dash Application

Mounted at /dashboard inside FastAPI via WSGIMiddleware.
Uses dcc.Interval for polling the FastAPI REST endpoints at /api/*.
"""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard.layouts.advisor_panel import advisor_panel_layout
from src.dashboard.layouts.equity_curve import equity_curve_layout
from src.dashboard.layouts.price_chart import price_chart_layout
from src.dashboard.layouts.risk_panel import risk_panel_layout
from src.dashboard.layouts.sip_panel import sip_panel_layout
from src.dashboard.layouts.trade_log import trade_log_layout

DISCLAIMER = (
    "⚠️ DISCLAIMER: Educational purposes only. Not financial advice. "
    "All signals and portfolio data are simulated. Past performance ≠ future results."
)


def create_dash_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.FLATLY],
        title="QuantAI Dashboard",
        update_title=None,
        suppress_callback_exceptions=True,
    )

    app.layout = dbc.Container([
        # Theme state
        dcc.Store(id="theme-store", data="light"),

        # Header
        dbc.Navbar(
            dbc.Container([
                dbc.NavbarBrand([
                    html.Span("⚡ QuantAI", className="fw-bold"),
                    html.Span(" ML Trading Dashboard", className="text-muted ms-1 small"),
                ]),
                dbc.Nav([
                    dbc.NavItem(dbc.Badge(
                        "PAPER TRADING ONLY",
                        color="warning",
                        text_color="dark",
                        className="ms-2",
                    )),
                    dbc.NavItem(
                        dbc.Button(
                            "🌙 Dark",
                            id="theme-toggle",
                            color="outline-light",
                            size="sm",
                            className="ms-3",
                        ),
                    ),
                ], navbar=True),
            ]),
            color="dark",
            dark=True,
            className="mb-4",
        ),

        # Disclaimer banner
        dbc.Alert(DISCLAIMER, color="warning", dismissable=True, className="mb-3"),

        # Tabs
        dbc.Tabs([
            dbc.Tab(label="Live Trading", tab_id="tab-live", children=[
                html.Div(className="mt-3", children=price_chart_layout()),
                html.Div(className="mt-3", children=trade_log_layout()),
            ]),
            dbc.Tab(label="Portfolio", tab_id="tab-portfolio", children=[
                html.Div(className="mt-3", children=equity_curve_layout()),
            ]),
            dbc.Tab(label="Backtesting", tab_id="tab-backtest", children=[
                html.Div(className="mt-3", children=risk_panel_layout()),
            ]),
            dbc.Tab(label="SIP Calculator", tab_id="tab-sip", children=[
                html.Div(className="mt-3", children=sip_panel_layout()),
            ]),
            dbc.Tab(label="Advisor", tab_id="tab-advisor", children=[
                html.Div(className="mt-3", children=advisor_panel_layout()),
            ]),
        ], id="main-tabs", active_tab="tab-live"),

        # Polling interval — fires every 3s
        dcc.Interval(id="interval-update", interval=3000, n_intervals=0),

    ], fluid=True)

    # Register all callbacks
    from src.dashboard.callbacks.advisor_callbacks import register_advisor_callbacks
    from src.dashboard.callbacks.backtest_callbacks import register_backtest_callbacks
    from src.dashboard.callbacks.portfolio_callbacks import register_portfolio_callbacks
    from src.dashboard.callbacks.price_callbacks import register_price_callbacks
    from src.dashboard.callbacks.sip_callbacks import register_sip_callbacks

    register_price_callbacks(app)
    register_portfolio_callbacks(app)
    register_backtest_callbacks(app)
    register_sip_callbacks(app)
    register_advisor_callbacks(app)

    from dash import Input, Output, State, callback_context
    import httpx

    @app.callback(
        Output("theme-store", "data"),
        Output("theme-toggle", "children"),
        Input("theme-toggle", "n_clicks"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_theme(n_clicks, current_theme):
        if current_theme == "light":
            return "dark", "☀️ Light"
        return "light", "🌙 Dark"

    # Trade log callback (inline since it's simple)

    @app.callback(
        Output("trade-log-table", "data"),
        Input("interval-update", "n_intervals"),
    )
    def update_trade_log(n):
        try:
            resp = httpx.get("http://localhost:8000/api/portfolio/trades", timeout=2)
            if resp.status_code == 200:
                return resp.json().get("trades", [])
        except Exception:
            pass
        return []

    return app
