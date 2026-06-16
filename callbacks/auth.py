import secrets

import dash
from dash import Input, Output, State, callback, ctx, html

from core import db
from core.i18n import t

_TOKEN_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _generate_token() -> str:
    """Генерирует высокоэнтропийный код, который удобно копировать человеку."""
    groups = []
    for _ in range(4):
        groups.append("".join(secrets.choice(_TOKEN_ALPHABET) for _ in range(5)))
    return "-".join(groups)


def _token_display(token: str):
    return html.Span(
        [html.Span(part, className="auth-token-part") for part in token.split("-")],
        className="auth-token-value",
    )


@callback(
    Output("auth-modal", "is_open"),
    Output("auth-generated-token", "children"),
    Output("auth-generated-block", "style"),
    Output("pending-token-store", "data"),
    Output("user-token-store", "data"),
    Output("auth-error-msg", "children"),
    Input("auth-open-btn", "n_clicks"),
    Input("auth-generate-btn", "n_clicks"),
    Input("auth-signin-btn", "n_clicks"),
    Input("auth-continue-btn", "n_clicks"),
    State("auth-token-input", "value"),
    State("pending-token-store", "data"),
    Input("lang-store", "data"),
    prevent_initial_call=True,
)
def handle_auth(n_open, n_generate, n_signin, n_continue, input_token, pending_token, lang):
    triggered = ctx.triggered_id

    if triggered == "auth-open-btn":
        return True, dash.no_update, {"display": "none"}, None, dash.no_update, ""

    if triggered == "auth-generate-btn":
        token = _generate_token()
        return True, _token_display(token), {"display": "block"}, token, dash.no_update, ""

    if triggered == "auth-signin-btn":
        normalized = db.normalize_token(input_token)
        if not normalized:
            return True, dash.no_update, dash.no_update, dash.no_update, dash.no_update, t("auth.error_invalid_format", lang)
        if not db.token_exists(normalized):
            return True, dash.no_update, dash.no_update, dash.no_update, dash.no_update, t("auth.error_not_found", lang)
        return False, dash.no_update, {"display": "none"}, None, normalized, ""

    if triggered == "auth-continue-btn":
        if pending_token:
            return False, dash.no_update, {"display": "none"}, None, pending_token, ""
        return False, dash.no_update, {"display": "none"}, None, dash.no_update, ""

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, ""


@callback(
    Output("user-id-store", "data"),
    Input("user-token-store", "data"),
    prevent_initial_call=False,
)
def resolve_user_id(token):
    return db.register_or_get_user(token)


@callback(
    Output("auth-token-badge", "children"),
    Output("auth-status-dot", "style"),
    Output("auth-open-btn", "children"),
    Input("user-token-store", "data"),
    Input("lang-store", "data"),
    prevent_initial_call=False,
)
def update_auth_badge(token, lang):
    normalized = db.normalize_token(token)
    if not normalized:
        return (
            t("auth.not_signed_in", lang),
            {"color": "#aaa", "fontSize": "8px", "marginRight": "6px"},
            t("auth.sign_in_create", lang),
        )

    short = f"{normalized[:11]}…"
    return (
        short,
        {"color": "#28b62c", "fontSize": "8px", "marginRight": "6px"},
        t("auth.change", lang),
    )


@callback(
    Output("auth-clipboard", "content"),
    Input("pending-token-store", "data"),
    Input("user-token-store", "data"),
    prevent_initial_call=False,
)
def update_clipboard_content(pending_token, current_token):
    return pending_token or current_token or ""


@callback(
    Output("export-pdf-btn", "disabled"),
    Output("export-pdf-btn", "title"),
    Output("preset-dropdown", "disabled"),
    Output("preset-load-btn", "disabled"),
    Output("preset-save-btn", "disabled"),
    Output("preset-save-as-btn", "disabled"),
    Output("preset-delete-btn", "disabled"),
    Input("user-id-store", "data"),
    Input("lang-store", "data"),
    prevent_initial_call=False,
)
def toggle_auth_controls(user_id, lang):
    locked = not bool(user_id)
    title = t("auth.sign_in_to_export", lang) if locked else ""
    return locked, title, locked, locked, locked, locked, locked
