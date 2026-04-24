import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from core.defaults import DEFAULT_APP_SETTINGS

def create_settings_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Application Settings", style={"fontSize": "16px", "fontWeight": 600}),
                className="preset-modal-header"
            ),
            dbc.ModalBody([
                dbc.Accordion([
                    # WEB 2D SETTINGS
                    dbc.AccordionItem([
                        dbc.Row([
                            dbc.Col(html.Label("Fill Color", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Input(id="set-web-2d-fill", type="color", value=DEFAULT_APP_SETTINGS["web_2d_fill_color"], size="sm"),
                                width=6
                            )
                        ], className="mb-2 align-items-center"),
                        dbc.Row([
                            dbc.Col(html.Label("Dimension Color", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Input(id="set-web-2d-dim", type="color", value=DEFAULT_APP_SETTINGS["web_2d_dim_color"], size="sm"),
                                width=6
                            )
                        ], className="align-items-center"),
                    ], title="Web 2D Settings"),

                    # WEB 3D SETTINGS
                    dbc.AccordionItem([
                        dbc.Row([
                            dbc.Col(html.Label("Model Base Color", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Input(id="set-web-3d-model-color", type="color", value=DEFAULT_APP_SETTINGS["web_3d_model_color"], size="sm"),
                                width=6
                            )
                        ], className="mb-2 align-items-center"),
                        html.Hr(className="my-2"),
                        html.Label("Surface Lighting", className="tablet-input-label mb-2"),
                        _make_slider("set-web-3d-ambient", "Ambient", 0, 1, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_ambient"]),
                        _make_slider("set-web-3d-diffuse", "Diffuse", 0, 1, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_diffuse"]),
                        _make_slider("set-web-3d-specular", "Specular", 0, 2, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_specular"]),
                        _make_slider("set-web-3d-roughness", "Roughness", 0, 1, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_roughness"]),
                        _make_slider("set-web-3d-fresnel", "Fresnel", 0, 5, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_fresnel"]),
                    ], title="Web 3D Settings"),

                    # PDF EXPORT SETTINGS
                    dbc.AccordionItem([
                        dbc.Row([
                            dbc.Col(html.Label("Orientation", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Select(
                                    id="set-pdf-orientation",
                                    options=[
                                        {"label": "Portrait", "value": "portrait"},
                                        {"label": "Landscape", "value": "landscape"}
                                    ],
                                    value=DEFAULT_APP_SETTINGS["pdf_orientation"],
                                    size="sm"
                                ),
                                width=6
                            )
                        ], className="mb-2 align-items-center"),
                        dbc.Row([
                            dbc.Col(html.Label("2D Fill Color", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Input(id="set-pdf-2d-fill", type="color", value=DEFAULT_APP_SETTINGS["pdf_2d_fill_color"], size="sm"),
                                width=6
                            )
                        ], className="mb-2 align-items-center"),
                        dbc.Row([
                            dbc.Col(html.Label("Dimension Font Size", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Select(
                                    id="set-pdf-dim-font-size",
                                    options=[
                                        {"label": "8 pt", "value": 8},
                                        {"label": "9 pt", "value": 9},
                                        {"label": "10 pt", "value": 10},
                                        {"label": "11 pt", "value": 11},
                                        {"label": "12 pt", "value": 12},
                                    ],
                                    value=DEFAULT_APP_SETTINGS["pdf_2d_dim_font_size"],
                                    size="sm"
                                ),
                                width=6
                            )
                        ], className="mb-2 align-items-center"),
                        dbc.Row([
                            dbc.Col(html.Label("Enable 2D Shading", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Checkbox(id="set-pdf-2d-shaded", value=DEFAULT_APP_SETTINGS["pdf_2d_shaded"]),
                                width=6
                            )
                        ], className="mb-2 align-items-center"),
                        dbc.Row([
                            dbc.Col(html.Label("Include 3D View", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Checkbox(id="set-pdf-include-3d", value=DEFAULT_APP_SETTINGS["pdf_include_3d"]),
                                width=6
                            )
                        ], className="mb-2 align-items-center"),
                        dbc.Row([
                            dbc.Col(html.Label("3D Model Quality", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Select(
                                    id="set-pdf-3d-quality",
                                    options=[
                                        {"label": "Low (Fast)", "value": "low"},
                                        {"label": "Medium (Balanced)", "value": "medium"},
                                        {"label": "High (Detailed)", "value": "high"}
                                    ],
                                    value=DEFAULT_APP_SETTINGS["pdf_3d_quality"],
                                    size="sm"
                                ),
                                width=6
                            )
                        ], className="mb-2 align-items-center"),
                        dbc.Row([
                            dbc.Col(html.Label("Created by", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Input(id="set-pdf-created-by", type="text", value=DEFAULT_APP_SETTINGS["pdf_created_by"], size="sm"),
                                width=6
                            )
                        ], className="mb-2 align-items-center"),
                        dbc.Row([
                            dbc.Col(html.Label("Approved by", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Input(id="set-pdf-approved-by", type="text", value=DEFAULT_APP_SETTINGS["pdf_approved_by"], size="sm"),
                                width=6
                            )
                        ], className="align-items-center"),
                    ], title="PDF Export Settings"),
                ], start_collapsed=False, flush=True)
            ]),
            dbc.ModalFooter(
                html.Div([
                    dbc.Button(
                        "Reset to Default",
                        id="btn-settings-reset",
                        outline=True,
                        color="secondary",
                        className="outline-soft-btn preset-modal-btn",
                    ),
                    html.Div([
                        dbc.Button(
                            "Cancel",
                            id="btn-settings-cancel",
                            outline=True,
                            color="secondary",
                            className="outline-soft-btn preset-modal-btn",
                        ),
                        dbc.Button(
                            "Save Settings",
                            id="btn-settings-save",
                            outline=True,
                            color="secondary",
                            className="outline-soft-btn preset-modal-btn",
                        ),
                    ], style={"display": "flex", "gap": "8px"}),
                ], style={"display": "flex", "width": "100%", "justifyContent": "space-between"}),
                style={"borderTop": "none", "padding": "0.5rem"},
            ),
        ],
        id="settings-modal",
        is_open=False,
        size="md",
        centered=True,
        className="preset-modal",
    )

def _make_slider(id_name, label, min_val, max_val, step, default_val):
    return dbc.Row([
        dbc.Col(html.Label(label, className="tablet-input-label mb-0"), width=4),
        dbc.Col(
            dcc.Slider(
                id=id_name,
                min=min_val,
                max=max_val,
                step=step,
                value=default_val,
                marks=None,
                updatemode="drag",
                className="p-0 m-0"
            ),
            width=6,
            style={"display": "flex", "alignItems": "center"}
        ),
        dbc.Col(
            dbc.Input(
                id=f"{id_name}-val",
                type="number",
                value=default_val,
                readonly=True,
                size="sm",
                style={"padding": "2px 4px", "textAlign": "center", "fontSize": "12px", "backgroundColor": "#f8f9fa", "cursor": "default", "height": "24px"}
            ),
            width=2,
            className="ps-1"
        )
    ], className="mb-1 align-items-center")