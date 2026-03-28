"""Callbacks for the AI Reasoning (multi-agent) dashboard tab."""

import httpx
import plotly.graph_objects as go
from dash import Input, Output, State, no_update

BASE_URL = "http://localhost:8000"

_DECISION_COLORS = {
    "BUY": "success",
    "SELL": "danger",
    "HOLD": "warning",
}


def _empty_figure(message: str = "No data") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=13, color="#999"),
    )
    fig.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=20, b=40))
    return fig


def _content_div(text: str) -> object:
    """Render agent brief text preserving newlines."""
    from dash import html

    if not text:
        from dash import html

        return html.Span("No content", className="text-muted")
    return html.Pre(text, style={"whiteSpace": "pre-wrap", "fontSize": "12px", "margin": 0})


def register_agent_callbacks(app):
    from dash import html

    @app.callback(
        Output("agent-analysis-id", "data"),
        Output("agent-status-msg", "children"),
        Output("agent-poll-interval", "disabled"),
        Input("agent-analyze-btn", "n_clicks"),
        State("agent-ticker-select", "value"),
        prevent_initial_call=True,
    )
    def trigger_analysis(n_clicks, ticker):
        if not ticker or not n_clicks:
            return no_update, no_update, True

        try:
            resp = httpx.post(
                f"{BASE_URL}/api/agents/analyze/{ticker}",
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                analysis_id = data.get("analysis_id")
                msg = html.Span(
                    [
                        html.Span("Running analysis... ", className="text-primary fw-bold"),
                        html.Small(f"ID: {analysis_id}", className="text-muted"),
                    ]
                )
                return analysis_id, msg, False  # enable polling
            else:
                return None, html.Span(f"Error: {resp.status_code}", className="text-danger"), True
        except Exception as exc:
            return None, html.Span(f"Request failed: {exc}", className="text-danger"), True

    @app.callback(
        Output("agent-quant-content", "children"),
        Output("agent-news-content", "children"),
        Output("agent-risk-content", "children"),
        Output("agent-pm-content", "children"),
        Output("agent-decision-badge", "children"),
        Output("agent-confidence-bar", "value"),
        Output("agent-confidence-bar", "label"),
        Output("agent-confidence-bar", "color"),
        Output("agent-reasoning-summary", "children"),
        Output("agent-status-msg", "children", allow_duplicate=True),
        Output("agent-poll-interval", "disabled", allow_duplicate=True),
        Input("agent-poll-interval", "n_intervals"),
        State("agent-analysis-id", "data"),
        State("agent-ticker-select", "value"),
        prevent_initial_call=True,
    )
    def poll_status(n_intervals, analysis_id, ticker):
        _no_change = (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )
        if not analysis_id:
            return _no_change

        try:
            resp = httpx.get(f"{BASE_URL}/api/agents/status/{analysis_id}", timeout=5)
        except Exception:
            return _no_change

        if resp.status_code != 200:
            return _no_change

        status_data = resp.json()
        status = status_data.get("status", "pending")

        if status == "running" or status == "pending":
            msg = html.Span("Agents deliberating...", className="text-primary")
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                msg,
                False,
            )

        if status == "error":
            error = status_data.get("error", "Unknown error")
            msg = html.Span(f"Analysis failed: {error}", className="text-danger")
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                msg,
                True,
            )

        if status == "complete":
            # Fetch full debate
            try:
                debate_resp = httpx.get(f"{BASE_URL}/api/agents/debate/{ticker}", timeout=5)
                debate = debate_resp.json() if debate_resp.status_code == 200 else {}
            except Exception:
                debate = {}

            agents = debate.get("agents", {})

            def _brief_text(key: str) -> str:
                brief = agents.get(key) or {}
                if isinstance(brief, dict):
                    return brief.get("content", "")
                return str(brief)

            quant_div = _content_div(_brief_text("quant"))
            news_div = _content_div(_brief_text("news"))
            risk_div = _content_div(_brief_text("risk"))
            pm_div = _content_div(_brief_text("portfolio_manager"))

            decision = status_data.get("decision", "HOLD") or "HOLD"
            confidence = status_data.get("confidence") or 0
            conf_pct = int(confidence * 100)
            badge_color = _DECISION_COLORS.get(decision, "secondary")
            summary = status_data.get("reasoning_summary", "")

            decision_badge = html.H3(
                decision,
                className=f"text-{badge_color} fw-bold",
            )

            bar_color = {"BUY": "success", "SELL": "danger", "HOLD": "warning"}.get(
                decision, "secondary"
            )
            msg = html.Span(
                [
                    html.Span("Analysis complete ", className="text-success fw-bold"),
                    html.Small(f"({conf_pct}% confidence)", className="text-muted"),
                ]
            )

            return (
                quant_div,
                news_div,
                risk_div,
                pm_div,
                decision_badge,
                conf_pct,
                f"{conf_pct}%",
                bar_color,
                summary,
                msg,
                True,  # disable polling
            )

        return _no_change

    @app.callback(
        Output("agent-accuracy-chart", "figure"),
        Input("agent-ticker-select", "value"),
        Input("agent-analyze-btn", "n_clicks"),
    )
    def update_accuracy_chart(ticker, _n):
        if not ticker:
            return _empty_figure("Select a ticker to see decision history")

        try:
            resp = httpx.get(f"{BASE_URL}/api/agents/history/{ticker}", timeout=5)
            if resp.status_code != 200:
                return _empty_figure("No history available")
            data = resp.json()
        except Exception:
            return _empty_figure("Could not load history")

        decisions = data.get("decisions", [])
        if not decisions:
            return _empty_figure(f"No analysis history for {ticker}")

        dates = [d.get("analyzed_at", "")[:10] for d in decisions]
        decision_labels = [d.get("decision", "HOLD") for d in decisions]
        confidence_vals = [int((d.get("confidence") or 0) * 100) for d in decisions]

        color_map = {"BUY": "#27AE60", "SELL": "#E74C3C", "HOLD": "#F39C12"}
        colors = [color_map.get(dec, "#999") for dec in decision_labels]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=dates,
                y=confidence_vals,
                marker_color=colors,
                text=decision_labels,
                textposition="outside",
                name="Confidence %",
            )
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=40, r=20, t=20, b=40),
            yaxis_title="Confidence %",
            yaxis_range=[0, 110],
            showlegend=False,
        )
        return fig
