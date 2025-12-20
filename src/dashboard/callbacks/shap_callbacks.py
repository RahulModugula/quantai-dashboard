import httpx
import plotly.graph_objects as go
from dash import Input, Output

BASE_URL = "http://localhost:8000"

_MODEL_COLORS = {
    "rf": "#4A90D9",
    "xgb": "#E67E22",
    "lgbm": "#27AE60",
}


def _empty_figure(message: str = "No model data available") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="#999"),
    )
    fig.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=20, b=40))
    return fig


def register_shap_callbacks(app):
    @app.callback(
        Output("shap-bar-chart", "figure"),
        Output("shap-model-chart", "figure"),
        Output("shap-status", "children"),
        Input("shap-refresh-btn", "n_clicks"),
        Input("shap-ticker-select", "value"),
        prevent_initial_call=False,
    )
    def update_shap_charts(n_clicks, ticker):
        if not ticker:
            return _empty_figure(), _empty_figure(), ""

        try:
            resp = httpx.get(
                f"{BASE_URL}/api/shap/importance/{ticker}",
                timeout=10,
            )
        except Exception as exc:
            msg = f"Request failed: {exc}"
            return _empty_figure(msg), _empty_figure(msg), msg

        if resp.status_code == 503:
            msg = "No trained model loaded."
            return _empty_figure(msg), _empty_figure(msg), msg

        if resp.status_code == 404:
            msg = f"No feature data found for {ticker}."
            return _empty_figure(msg), _empty_figure(msg), msg

        if resp.status_code != 200:
            msg = f"API error {resp.status_code}."
            return _empty_figure(msg), _empty_figure(msg), msg

        data = resp.json()
        feature_importance = data.get("feature_importance", [])
        per_model = data.get("per_model", {})

        # --- Horizontal bar chart: top 15 features ---
        top15 = feature_importance[:15]
        if top15:
            features = [item["feature"] for item in reversed(top15)]
            values = [item["shap_value"] for item in reversed(top15)]
            bar_fig = go.Figure(
                go.Bar(
                    x=values,
                    y=features,
                    orientation="h",
                    marker_color="#4A90D9",
                )
            )
            bar_fig.update_layout(
                template="plotly_white",
                margin=dict(l=40, r=20, t=20, b=40),
                xaxis_title="Mean |SHAP|",
            )
        else:
            bar_fig = _empty_figure()

        # --- Grouped bar chart: per-model top 10 ---
        top10_features = [item["feature"] for item in feature_importance[:10]]
        model_fig = go.Figure()
        for model_name in ("rf", "xgb", "lgbm"):
            model_data = per_model.get(model_name, {})
            if not model_data:
                continue
            y_vals = [model_data.get(f, 0.0) for f in top10_features]
            model_fig.add_trace(
                go.Bar(
                    name=model_name.upper(),
                    x=top10_features,
                    y=y_vals,
                    marker_color=_MODEL_COLORS.get(model_name, "#999"),
                )
            )

        if model_fig.data:
            model_fig.update_layout(
                barmode="group",
                template="plotly_white",
                margin=dict(l=40, r=20, t=20, b=60),
                yaxis_title="Mean |SHAP|",
                xaxis_tickangle=-30,
                legend=dict(orientation="h", y=1.05),
            )
        else:
            model_fig = _empty_figure()

        status = f"Loaded SHAP importance for {ticker} — {len(feature_importance)} features."
        return bar_fig, model_fig, status
