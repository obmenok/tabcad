from dash import html, dcc
import dash_bootstrap_components as dbc

from components.sidebar import make_input
from core.defaults import BASE_DEFAULTS


def _panel_block(children, min_height=None):
    style = {"overflow": "visible", "position": "relative"}
    if min_height:
        style["minHeight"] = min_height
    return html.Div(children, className="py-2 px-3 bg-light border rounded h-100", style=style)


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
                            dbc.Button("Save", id="preset-save-btn", color="light", class_name="plotly-toolbar-btn"),
                            dbc.Button("Save As", id="preset-save-as-btn", color="light", class_name="plotly-toolbar-btn"),
                            dbc.Button("Delete", id="preset-delete-btn", color="light", class_name="plotly-toolbar-btn"),
                        ],
                        size="sm",
                        className="plotly-toolbar-group preset-btn-group segmented-btn-group",
                    ),
                ],
                className="mb-3",
            ),
            html.Div(
                [
                    html.Label(
                        "Physical Parameters",
                        id="label-physical-title",
                        className="fw-bold mb-1",
                    ),
                    make_input(
                        "input-density",
                        "Tablet Density, mg/mm3",
                        BASE_DEFAULTS["density"],
                        step=0.01,
                        min_value=0.01,
                        debounce=True,
                    ),
                    make_input(
                        "input-weight",
                        "Tablet Weight, mg",
                        None,
                        step=0.01,
                        min_value=0.0,
                        debounce=True,
                    ),
                ],
                className="mb-3",
            ),
            html.Div(
                [
                    html.Label("Tip force", id="label-tip-force-title", className="fw-bold mb-1"),
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(
                                "Steel type",
                                id="label-tip-force-steel",
                                className="tablet-input-label",
                                style={"width": "70%"},
                            ),
                            dbc.Select(
                                id="input-tip-force-steel",
                                options=[
                                    {"label": "S7", "value": "S7"},
                                    {"label": "D2", "value": "D2"},
                                ],
                                value=BASE_DEFAULTS["tip_force_steel"],
                                size="sm",
                                className="tablet-input-control",
                            ),
                        ],
                        className="mb-2 input-group-sm",
                        size="sm",
                    ),
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(
                                "Max tip force",
                                id="label-tip-force-value",
                                className="tablet-input-label",
                                style={"width": "70%"},
                            ),
                            dbc.Input(
                                id="tip-force-value",
                                type="text",
                                value="N/A",
                                readonly=True,
                                size="sm",
                                className="tablet-input-control",
                            ),
                        ],
                        className="mb-2 input-group-sm",
                        size="sm",
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
                ]
            ),
        ],
        className="py-2 px-3 bg-light border rounded h-100",
    )

    return html.Div(
        [
            info_block,
            preset_modal,
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
                        className="flex-nowrap align-items-center gap-2 plotly-toolbar-wrap",
                        style={
                            "position": "absolute",
                            "top": "8px",
                            "left": "8px",
                            "zIndex": 5000,
                            "background": "rgba(255,255,255,0.92)",
                            "borderRadius": "6px",
                            "padding": "6px",
                            "overflow": "visible",
                        },
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
                        className="flex-nowrap align-items-center gap-2 plotly-toolbar-wrap",
                        style={
                            "position": "absolute",
                            "top": "8px",
                            "right": "8px",
                            "zIndex": 5000,
                            "background": "rgba(255,255,255,0.92)",
                            "borderRadius": "6px",
                            "padding": "6px",
                            "overflow": "visible",
                        },
                    ),
                    html.Div(
                        dbc.ButtonGroup(
                            [
                                dbc.DropdownMenu(
                                    id="plotly-view-menu",
                                    label=html.Span(
                                        [
                                            html.Span(className="apollo-icon av-i-view av-view-icon"),
                                            html.Span("View"),
                                        ],
                                        className="d-inline-flex align-items-center av-view-label",
                                    ),
                                    color="light",
                                    className="plotly-toolbar-btn",
                                    toggle_style={"minWidth": "104px"},
                                    children=[
                                        dbc.DropdownMenuItem(
                                            html.Span(
                                                [html.Span(className="apollo-icon av-i-front av-menu-icon"), "Front"]
                                            ),
                                            id="plotly-view-front",
                                        ),
                                        dbc.DropdownMenuItem(
                                            html.Span(
                                                [html.Span(className="apollo-icon av-i-back av-menu-icon"), "Back"]
                                            ),
                                            id="plotly-view-back",
                                        ),
                                        dbc.DropdownMenuItem(
                                            html.Span(
                                                [html.Span(className="apollo-icon av-i-left av-menu-icon"), "Left"]
                                            ),
                                            id="plotly-view-left",
                                        ),
                                        dbc.DropdownMenuItem(
                                            html.Span(
                                                [html.Span(className="apollo-icon av-i-right av-menu-icon"), "Right"]
                                            ),
                                            id="plotly-view-right",
                                        ),
                                        dbc.DropdownMenuItem(
                                            html.Span(
                                                [html.Span(className="apollo-icon av-i-top av-menu-icon"), "Top"]
                                            ),
                                            id="plotly-view-top",
                                        ),
                                        dbc.DropdownMenuItem(
                                            html.Span(
                                                [html.Span(className="apollo-icon av-i-bottom av-menu-icon"), "Bottom"]
                                            ),
                                            id="plotly-view-bottom",
                                        ),
                                        dbc.DropdownMenuItem(
                                            html.Span(
                                                [
                                                    html.Span(className="apollo-icon av-i-isometric av-menu-icon"),
                                                    "Isometric",
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
                        className="flex-nowrap align-items-center gap-2 plotly-toolbar-wrap",
                        style={
                            "position": "absolute",
                            "top": "8px",
                            "right": "8px",
                            "zIndex": 5000,
                            "background": "rgba(255,255,255,0.92)",
                            "borderRadius": "6px",
                            "padding": "6px",
                            "overflow": "visible",
                            "display": "none",
                        },
                    ),
                    html.Div(
                        html.Img(
                            id="tablet-drawing",
                            src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==",
                            style={"width": "100%", "height": "100%", "object-fit": "contain"},
                        ),
                        id="viewer-2d-layer",
                        style={"height": "100%", "width": "100%"},
                    ),
                    html.Div(
                        html.Div(id="tablet-3d", style={"height": "100%"}),
                        id="viewer-3d-layer",
                        style={"height": "100%", "width": "100%", "display": "none"},
                    ),
                    dcc.Store(id="viewer-mode-store", data="2d"),
                    dcc.Store(id="drawing-2d-shaded", data=False),
                    dcc.Store(id="drawing-2d-png-src"),
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
                className="border rounded bg-white p-2",
                style={"height": "100%", "position": "relative", "overflow": "visible"},
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
