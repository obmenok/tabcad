from dash import dcc, html
import dash_bootstrap_components as dbc


def auth_stores():
    return [
        dcc.Store(id="user-token-store", storage_type="local"),
        dcc.Store(id="user-id-store"),
        dcc.Store(id="pending-token-store"),
    ]


def auth_status_panel():
    return html.Div(
        [
            html.Div(
                "Access Code",
                id="auth-status-title",
                className="fw-bold text-secondary mb-2",
                style={"fontSize": "1rem"},
            ),
            html.Div(
                [
                    html.Span("●", id="auth-status-dot", className="auth-status-dot"),
                    html.Span("Not signed in", id="auth-token-badge", className="auth-token-badge"),
                    dbc.Button(
                        "Sign in / Create",
                        id="auth-open-btn",
                        color="link",
                        size="sm",
                        className="auth-change-btn",
                    ),
                ],
                className="auth-status-bar",
            ),
        ],
        className="auth-panel mb-2",
    )


def auth_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    "Access Code",
                    id="auth-modal-title",
                    style={"fontSize": "16px", "fontWeight": 600},
                ),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    html.P(
                        "Use an access code to save presets and generate PDF files. "
                        "No email or personal data is required.",
                        id="auth-modal-desc",
                        className="text-secondary mb-0",
                        style={"fontSize": "14px"},
                    ),
                    html.Div(
                        [
                            dbc.Input(
                                id="auth-token-input",
                                placeholder="ABCDE-12345-FGHIJ-67890",
                                maxLength=23,
                                className="auth-token-input",
                            ),
                            dbc.Button(
                                "Sign in",
                                id="auth-signin-btn",
                                outline=True,
                                color="secondary",
                                className="outline-soft-btn preset-modal-btn",
                            ),
                        ],
                        className="auth-signin-row",
                    ),
                    html.Div(
                        id="auth-error-msg",
                        className="text-danger mb-2",
                        style={"fontSize": "14px"},
                    ),
                    html.Hr(className="my-2"),
                    dbc.Button(
                        "Create new code",
                        id="auth-generate-btn",
                        outline=True,
                        color="secondary",
                        className="outline-soft-btn preset-modal-btn w-100 mb-2",
                    ),
                    html.Div(
                        [
                            html.Div(
                                id="auth-generated-token",
                                className="auth-generated-token",
                            ),
                            dcc.Clipboard(
                                "Copy",
                                id="auth-clipboard",
                                className="auth-copy-clipboard w-100 mb-2",
                            ),
                            html.P(
                                "Save this code — it cannot be recovered later.",
                                id="auth-modal-warning",
                                className="text-secondary mb-0",
                                style={"fontSize": "14px"},
                            ),
                        ],
                        id="auth-generated-block",
                        style={"display": "none"},
                    ),
                ]
            ),
            dbc.ModalFooter(
                dbc.Button(
                    "Continue",
                    id="auth-continue-btn",
                    outline=True,
                    color="secondary",
                    className="outline-soft-btn preset-modal-btn",
                ),
                style={"justifyContent": "flex-end", "borderTop": "none"},
            ),
        ],
        id="auth-modal",
        is_open=False,
        centered=True,
        className="preset-modal auth-modal",
    )
