from dash import html, dcc
import dash_bootstrap_components as dbc
from components.auth import auth_modal, auth_status_panel, auth_stores
from core.defaults import DEFAULT_APP_SETTINGS


def _panel_block(children, min_height=None):
    style = {"overflow": "visible", "position": "relative"}
    if min_height:
        style["minHeight"] = min_height
    return html.Div(children, className="py-2 px-3 bg-light border rounded h-100", style=style)


def _settings_row(label, control):
    return dbc.InputGroup(
        [
            dbc.InputGroupText(
                label,
                className="tablet-input-label",
                style={"width": "70%"},
            ),
            html.Div(
                control,
                className="tablet-input-control settings-mock-control-cell",
            ),
        ],
        className="mb-2 input-group-sm",
        size="sm",
    )


def _settings_select_row(label, options, value, id):
    return _settings_row(
        label,
        dbc.Select(
            id=id,
            options=options,
            value=value,
            size="sm",
            className="settings-mock-input settings-mock-select",
        ),
    )


def _settings_preview_panel():
    return html.Div(
        [
            html.Div(
                "PDF Export",
                id="settings-title",
                className="fw-bold text-secondary mb-2",
                style={"fontSize": "1rem"},
            ),
            html.Div(
                [
                    _settings_select_row(
                        html.Span("Orientation", id="settings-orientation-label"),
                        [
                            {"label": "Portrait", "value": "portrait"},
                            {"label": "Landscape", "value": "landscape"},
                        ],
                        DEFAULT_APP_SETTINGS["pdf_orientation"],
                        id="set-pdf-orientation",
                    ),
                    _settings_row(
                        html.Span("2D Fill Color", id="settings-pdf-2d-fill-label"),
                        dbc.Input(
                            id="set-pdf-2d-fill",
                            type="color",
                            value=DEFAULT_APP_SETTINGS["pdf_2d_fill_color"],
                            size="sm",
                            className="settings-mock-color",
                            debounce=True,
                        ),
                    ),
                    _settings_select_row(
                        html.Span("Dimension Font Size", id="settings-dim-font-size-label"),
                        [
                            {"label": "8 pt", "value": 8},
                            {"label": "9 pt", "value": 9},
                            {"label": "10 pt", "value": 10},
                            {"label": "11 pt", "value": 11},
                            {"label": "12 pt", "value": 12},
                        ],
                        DEFAULT_APP_SETTINGS["pdf_2d_dim_font_size"],
                        id="set-pdf-dim-font-size",
                    ),
                    _settings_row(
                        html.Span("Enable 2D Shading", id="settings-pdf-2d-shaded-label"),
                        dbc.Checkbox(
                            id="set-pdf-2d-shaded",
                            value=DEFAULT_APP_SETTINGS["pdf_2d_shaded"],
                            className="settings-mock-check",
                        ),
                    ),
                    _settings_row(
                        html.Span("Include 3D View", id="settings-pdf-include-3d-label"),
                        dbc.Checkbox(
                            id="set-pdf-include-3d",
                            value=DEFAULT_APP_SETTINGS["pdf_include_3d"],
                            className="settings-mock-check",
                        ),
                    ),
                    _settings_select_row(
                        html.Span("3D Model Quality", id="settings-pdf-3d-quality-label"),
                        [
                            {"label": "Low", "value": "low"},
                            {"label": "Medium", "value": "medium"},
                            {"label": "High", "value": "high"},
                        ],
                        DEFAULT_APP_SETTINGS["pdf_3d_quality"],
                        id="set-pdf-3d-quality",
                    ),
                    _settings_row(
                        html.Span("Created by", id="settings-pdf-created-by-label"),
                        dbc.Input(
                            id="set-pdf-created-by",
                            type="text",
                            value=DEFAULT_APP_SETTINGS["pdf_created_by"],
                            size="sm",
                            className="settings-mock-input",
                            debounce=True,
                        ),
                    ),
                    _settings_row(
                        html.Span("Approved by", id="settings-pdf-approved-by-label"),
                        dbc.Input(
                            id="set-pdf-approved-by",
                            type="text",
                            value=DEFAULT_APP_SETTINGS["pdf_approved_by"],
                            size="sm",
                            className="settings-mock-input",
                            debounce=True,
                        ),
                    ),
                ],
                className="dimensions-table-block settings-mock-table mb-3",
            ),
            dbc.Button(
                "Generate PDF",
                id="export-pdf-btn",
                outline=True,
                color="secondary",
                className="outline-soft-btn preset-modal-btn w-100 mt-2",
            ),
            html.Hr(className="my-3"),
            dbc.Button(
                "Reset Settings",
                id="btn-settings-reset",
                outline=True,
                color="secondary",
                className="outline-soft-btn preset-modal-btn w-100",
            ),
            html.Div(
                [
                    html.Span("Send Feedback: ", id="feedback-label"),
                    html.A(
                        "bs26@ya.ru",
                        href="mailto:bs26@ya.ru?subject=TabletCAD%20Feedback",
                        className="feedback-mail-link",
                    ),
                ],
                className="feedback-mail-row",
            ),
            dcc.Download(id="download-pdf"),
        ],
        className="settings-preview-block",
    )


EMPTY_PRESET_OPTION = {
    "label": "No presets saved",
    "value": "__no_presets__",
    "disabled": True,
}


def create_info_panel():
    preset_modal = dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    "Save Preset As",
                    id="preset-modal-title",
                    style={"fontSize": "16px", "fontWeight": 600},
                ),
                className="preset-modal-header",
            ),
            dbc.ModalBody(
                dbc.Input(
                    id="preset-name-input",
                    placeholder="Enter preset name...",
                    type="text",
                    style={"fontSize": "14px"},
                ),
                style={"borderBottom": "none"},
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Save",
                        id="preset-modal-save-btn",
                        outline=True,
                        color="secondary",
                        className="outline-soft-btn preset-modal-btn",
                    ),
                    dbc.Button(
                        "Cancel",
                        id="preset-modal-cancel-btn",
                        outline=True,
                        color="secondary",
                        className="outline-soft-btn preset-modal-btn",
                    ),
                ],
                style={"justifyContent": "flex-end", "borderTop": "none", "gap": "8px"},
            ),
        ],
        id="preset-save-modal",
        is_open=False,
        centered=True,
        className="preset-modal",
    )

    info_block = html.Div(
        [
            html.Div(
                [
                    auth_status_panel(),
                    html.Div(
                        "Saved Presets",
                        id="presets-title",
                        className="fw-bold text-secondary mb-2",
                        style={"fontSize": "1rem"},
                    ),
                    html.Div(
                        dcc.Dropdown(
                            id="preset-dropdown",
                            options=[EMPTY_PRESET_OPTION],
                            value=None,
                            placeholder="Select preset...",
                            clearable=False,
                            searchable=False,
                            className="small-dropdown mb-2",
                            style={"fontSize": "0.85rem"},
                        ),
                        style={"overflow": "visible", "height": "40px"},
                    ),
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                "Load",
                                id="preset-load-btn",
                                color="light",
                                class_name="plotly-toolbar-btn",
                            ),
                            dbc.Button(
                                "Save",
                                id="preset-save-btn",
                                color="light",
                                class_name="plotly-toolbar-btn",
                            ),
                            dbc.Button(
                                "Save As",
                                id="preset-save-as-btn",
                                color="light",
                                class_name="plotly-toolbar-btn",
                            ),
                            dbc.Button(
                                "Delete",
                                id="preset-delete-btn",
                                color="light",
                                class_name="plotly-toolbar-btn",
                            ),
                        ],
                        size="sm",
                        className="plotly-toolbar-group preset-btn-group segmented-btn-group",
                    ),
                    html.Div(
                        id="preset-limit-msg",
                        className="text-secondary mt-1",
                        style={"fontSize": "0.75rem"},
                    ),
                ],
                className="mb-3",
            ),
            html.Div(
                [
                    html.Div(
                        id="calc-output",
                        className="h-100",
                        style={"minHeight": "125px"},
                    )
                ],
                className="mb-3",
            ),
            _settings_preview_panel(),
        ],
        className="py-2 px-0",
    )

    return html.Div(
        [
            info_block,
            preset_modal,
            auth_modal(),
            *auth_stores(),
        ],
        className="h-100",
        style={"overflow": "visible"},
    )


def create_middle_panel():
    return create_info_panel()


def create_model_panel():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            "2D",
                                            id="viewer-mode-2d-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn active",
                                            title="2D View",
                                            n_clicks=0,
                                        ),
                                        dbc.Button(
                                            "3D",
                                            id="viewer-mode-3d-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn",
                                            title="3D View",
                                            n_clicks=0,
                                        ),
                                    ],
                                    size="sm",
                                    className="plotly-toolbar-group segmented-btn-group",
                                ),
                                className=(
                                    "viewer-toolbar-cluster viewer-toolbar-cluster-left "
                                    "flex-nowrap align-items-center gap-2 plotly-toolbar-wrap"
                                ),
                            ),
                            html.Div(
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            html.Span(className="apollo-icon av-i-shaded"),
                                            id="drawing-shaded-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn plotly-toggle-btn",
                                            n_clicks=0,
                                            title="Shaded",
                                        ),
                                        dbc.Button(
                                            html.Span(className="apollo-icon av-i-fullscreen"),
                                            id="drawing-fullscreen-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn",
                                            title="Full screen",
                                        ),
                                        dbc.Button(
                                            html.Span("PNG", style={"fontWeight": "bold", "fontSize": "0.8rem"}),
                                            id="drawing-download-png-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn",
                                            title="Download PNG",
                                        ),
                                        dbc.Button(
                                            html.Span("SVG", style={"fontWeight": "bold", "fontSize": "0.8rem"}),
                                            id="drawing-download-svg-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn",
                                            title="Download SVG",
                                        ),
                                    ],
                                    size="sm",
                                    className="plotly-toolbar-group",
                                ),
                                id="viewer-toolbar-2d",
                                className=(
                                    "viewer-toolbar-cluster viewer-toolbar-cluster-right "
                                    "flex-nowrap align-items-center gap-2 plotly-toolbar-wrap"
                                ),
                            ),
                            html.Div(
                                dbc.ButtonGroup(
                                    [
                                        dbc.DropdownMenu(
                                            id="plotly-view-menu",
                                            label=html.Span(
                                                [
                                                    html.Span(className="apollo-icon av-i-view av-view-icon"),
                                                    html.Span("View", id="plotly-view-label"),
                                                ],
                                                className="d-inline-flex align-items-center av-view-label",
                                            ),
                                            color="light",
                                            className="plotly-toolbar-btn",
                                            toggle_style={"minWidth": "104px", "fontSize": "14px"},
                                            children=[
                                                dbc.DropdownMenuItem(
                                                    html.Span(
                                                        [
                                                            html.Span(
                                                                className="apollo-icon av-i-front av-menu-icon"
                                                            ),
                                                            html.Span("Front", id="plotly-view-front-label"),
                                                        ]
                                                    ),
                                                    id="plotly-view-front",
                                                ),
                                                dbc.DropdownMenuItem(
                                                    html.Span(
                                                        [
                                                            html.Span(
                                                                className="apollo-icon av-i-back av-menu-icon"
                                                            ),
                                                            html.Span("Back", id="plotly-view-back-label"),
                                                        ]
                                                    ),
                                                    id="plotly-view-back",
                                                ),
                                                dbc.DropdownMenuItem(
                                                    html.Span(
                                                        [
                                                            html.Span(
                                                                className="apollo-icon av-i-left av-menu-icon"
                                                            ),
                                                            html.Span("Left", id="plotly-view-left-label"),
                                                        ]
                                                    ),
                                                    id="plotly-view-left",
                                                ),
                                                dbc.DropdownMenuItem(
                                                    html.Span(
                                                        [
                                                            html.Span(
                                                                className="apollo-icon av-i-right av-menu-icon"
                                                            ),
                                                            html.Span("Right", id="plotly-view-right-label"),
                                                        ]
                                                    ),
                                                    id="plotly-view-right",
                                                ),
                                                dbc.DropdownMenuItem(
                                                    html.Span(
                                                        [
                                                            html.Span(
                                                                className="apollo-icon av-i-top av-menu-icon"
                                                            ),
                                                            html.Span("Top", id="plotly-view-top-label"),
                                                        ]
                                                    ),
                                                    id="plotly-view-top",
                                                ),
                                                dbc.DropdownMenuItem(
                                                    html.Span(
                                                        [
                                                            html.Span(
                                                                className="apollo-icon av-i-bottom av-menu-icon"
                                                            ),
                                                            html.Span("Bottom", id="plotly-view-bottom-label"),
                                                        ]
                                                    ),
                                                    id="plotly-view-bottom",
                                                ),
                                                dbc.DropdownMenuItem(
                                                    html.Span(
                                                        [
                                                            html.Span(
                                                                className="apollo-icon av-i-isometric av-menu-icon"
                                                            ),
                                                            html.Span(
                                                                "Isometric",
                                                                id="plotly-view-isometric-label",
                                                            ),
                                                        ]
                                                    ),
                                                    id="plotly-view-isometric",
                                                ),
                                            ],
                                        ),
                                        dbc.Button(
                                            html.Span(className="apollo-icon av-i-edge"),
                                            id="plotly-edge-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn plotly-toggle-btn",
                                            n_clicks=0,
                                            title="Edge",
                                        ),
                                        dbc.Button(
                                            html.Span(className="apollo-icon av-i-bbox"),
                                            id="plotly-bbox-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn plotly-toggle-btn",
                                            n_clicks=0,
                                            title="Boundary box",
                                        ),
                                        dbc.Button(
                                            html.Span(className="apollo-icon av-i-fullscreen"),
                                            id="plotly-fullscreen-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn",
                                            title="Full screen",
                                        ),
                                        dbc.Button(
                                            html.Span("PNG", style={"fontWeight": "bold", "fontSize": "0.8rem"}),
                                            id="plotly-screenshot-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn",
                                            title="Download PNG",
                                        ),
                                        dbc.Button(
                                            html.Span("STL", style={"fontWeight": "bold", "fontSize": "0.8rem"}),
                                            id="plotly-stl-btn",
                                            color="light",
                                            class_name="plotly-toolbar-btn",
                                            title="Download STL",
                                        ),
                                    ],
                                    size="sm",
                                    className="plotly-toolbar-group",
                                ),
                                id="viewer-toolbar-3d",
                                className=(
                                    "viewer-toolbar-cluster viewer-toolbar-cluster-right "
                                    "flex-nowrap align-items-center gap-2 plotly-toolbar-wrap"
                                ),
                                style={"display": "none"},
                            ),
                        ],
                        className="viewer-top-toolbar",
                    ),
                    html.Div(
                        html.Img(
                            id="tablet-drawing",
                            src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==",
                            style={"width": "100%", "height": "100%", "object-fit": "contain"},
                        ),
                        id="viewer-2d-layer",
                        className="viewer-content-layer",
                        style={"height": "100%", "width": "100%"},
                    ),
                    html.Div(
                        html.Div(id="tablet-3d", className="viewer-plotly-host", style={"height": "100%"}),
                        id="viewer-3d-layer",
                        className="viewer-content-layer",
                        style={"height": "100%", "width": "100%", "display": "none"},
                    ),

                    html.Div(
                        [
                            html.Span(
                                [
                                    html.Span(
                                        "Fill Color:",
                                        id="viewer-fill-color-label",
                                        className="viewer-settings-label me-1",
                                    ),
                                    dbc.Input(
                                        id="set-web-2d-fill",
                                        type="color",
                                        value=DEFAULT_APP_SETTINGS["web_2d_fill_color"],
                                        size="sm",
                                        className="toolbar-color-picker",
                                    ),
                                ],
                                className="viewer-settings-field",
                            ),
                            html.Span(
                                [
                                    html.Span(
                                        "Dimension Color:",
                                        id="viewer-dimension-color-label",
                                        className="viewer-settings-label me-1",
                                    ),
                                    dbc.Input(
                                        id="set-web-2d-dim",
                                        type="color",
                                        value=DEFAULT_APP_SETTINGS["web_2d_dim_color"],
                                        size="sm",
                                        className="toolbar-color-picker",
                                    ),
                                ],
                                className="viewer-settings-field",
                            ),
                        ],
                        id="viewer-settings-2d",
                        className="viewer-settings-toolbar align-items-center plotly-toolbar-wrap",
                        style={
                            "position": "absolute",
                            "bottom": "8px",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "zIndex": 5000,
                            "background": "rgba(255,255,255,0.92)",
                            "borderRadius": "6px",
                            "padding": "6px 12px",
                            "display": "flex",
                        },
                    ),
                    html.Div(
                        [
                            html.Span(
                                [
                                    html.Span(
                                        "Model Color:",
                                        id="viewer-model-color-label",
                                        className="viewer-settings-label me-1",
                                    ),
                                    dbc.Input(
                                        id="set-web-3d-model-color",
                                        type="color",
                                        value=DEFAULT_APP_SETTINGS["web_3d_model_color"],
                                        size="sm",
                                        className="toolbar-color-picker",
                                    ),
                                ],
                                className="viewer-settings-field",
                            ),
                            html.Span(
                                [
                                    html.Span(
                                        "Ambient:",
                                        id="viewer-ambient-label",
                                        className="viewer-settings-label me-1",
                                    ),
                                    dbc.Input(
                                        id="set-web-3d-ambient",
                                        type="number",
                                        value=DEFAULT_APP_SETTINGS["web_3d_lighting_ambient"],
                                        step=0.1,
                                        size="sm",
                                        className="viewer-settings-number",
                                    ),
                                ],
                                className="viewer-settings-field",
                            ),
                            html.Span(
                                [
                                    html.Span(
                                        "Diffuse:",
                                        id="viewer-diffuse-label",
                                        className="viewer-settings-label me-1",
                                    ),
                                    dbc.Input(
                                        id="set-web-3d-diffuse",
                                        type="number",
                                        value=DEFAULT_APP_SETTINGS["web_3d_lighting_diffuse"],
                                        step=0.1,
                                        size="sm",
                                        className="viewer-settings-number",
                                    ),
                                ],
                                className="viewer-settings-field",
                            ),
                            html.Span(
                                [
                                    html.Span(
                                        "Specular:",
                                        id="viewer-specular-label",
                                        className="viewer-settings-label me-1",
                                    ),
                                    dbc.Input(
                                        id="set-web-3d-specular",
                                        type="number",
                                        value=DEFAULT_APP_SETTINGS["web_3d_lighting_specular"],
                                        step=0.1,
                                        size="sm",
                                        className="viewer-settings-number",
                                    ),
                                ],
                                className="viewer-settings-field",
                            ),
                            html.Span(
                                [
                                    html.Span(
                                        "Roughness:",
                                        id="viewer-roughness-label",
                                        className="viewer-settings-label me-1",
                                    ),
                                    dbc.Input(
                                        id="set-web-3d-roughness",
                                        type="number",
                                        value=DEFAULT_APP_SETTINGS["web_3d_lighting_roughness"],
                                        step=0.1,
                                        size="sm",
                                        className="viewer-settings-number",
                                    ),
                                ],
                                className="viewer-settings-field",
                            ),
                        ],
                        id="viewer-settings-3d",
                        className="viewer-settings-toolbar align-items-center plotly-toolbar-wrap",
                        style={
                            "position": "absolute",
                            "bottom": "8px",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "zIndex": 5000,
                            "background": "rgba(255,255,255,0.92)",
                            "borderRadius": "6px",
                            "padding": "6px 12px",
                            "display": "none",
                        },
                    ),
                    dcc.Store(id="viewer-mode-store", data="2d"),
                    dcc.Store(id="drawing-2d-shaded", data=False),
                    dcc.Store(id="drawing-2d-png-src"),
                    dcc.Store(id="mesh-data-store"),
                    dcc.Store(id="plotly-view-preset", data="isometric"),
                    dcc.Store(id="plotly-show-edges", data=False),
                    dcc.Store(id="plotly-show-bbox", data=False),
                    html.Div(id="drawing-fullscreen-signal", style={"display": "none"}),
                    html.Div(id="plotly-fullscreen-signal", style={"display": "none"}),
                    html.Div(id="plotly-screenshot-signal", style={"display": "none"}),
                    dcc.Download(id="download-2d"),
                    dcc.Download(id="download-stl"),
                ],
                id="viewer-viewport-panel",
                className="viewer-shell border rounded bg-white p-2",
                style={"height": "100%", "position": "relative", "overflow": "hidden"},
            )
        ],
        className="h-100",
    )


def create_viewer():
    return html.Div(
        [
            create_model_panel(),
            create_info_panel(),
        ],
        className="h-100",
        style={"minHeight": 0},
    )


def create_right_panel():
    return create_info_panel()
