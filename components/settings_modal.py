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
                        html.Label("Surface Lighting (Top)", className="fw-bold mb-2", style={"fontSize": "12px"}),
                        _make_slider("set-web-3d-ambient", "Ambient", 0, 1, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_ambient"]),
                        _make_slider("set-web-3d-diffuse", "Diffuse", 0, 1, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_diffuse"]),
                        _make_slider("set-web-3d-specular", "Specular", 0, 2, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_specular"]),
                        _make_slider("set-web-3d-roughness", "Roughness", 0, 1, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_roughness"]),
                        _make_slider("set-web-3d-fresnel", "Fresnel", 0, 5, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_fresnel"]),
                        
                        html.Hr(className="my-2"),
                        html.Label("Surface Lighting (Bottom/Side)", className="fw-bold mb-2", style={"fontSize": "12px"}),
                        _make_slider("set-web-3d-bot-ambient", "Ambient", 0, 1, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_bot_ambient"]),
                        _make_slider("set-web-3d-bot-diffuse", "Diffuse", 0, 1, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_bot_diffuse"]),
                        _make_slider("set-web-3d-bot-specular", "Specular", 0, 2, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_bot_specular"]),
                        _make_slider("set-web-3d-bot-roughness", "Roughness", 0, 1, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_bot_roughness"]),
                        _make_slider("set-web-3d-bot-fresnel", "Fresnel", 0, 5, 0.1, DEFAULT_APP_SETTINGS["web_3d_lighting_bot_fresnel"]),
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
                            dbc.Col(html.Label("Enable 2D Shading", className="tablet-input-label"), width=6),
                            dbc.Col(
                                dbc.Checkbox(id="set-pdf-2d-shaded", value=DEFAULT_APP_SETTINGS["pdf_2d_shaded"]),
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
            dbc.ModalFooter([
                dbc.Button("Reset to Default", id="btn-settings-reset", color="danger", outline=True, size="sm", className="me-auto"),
                dbc.Button("Cancel", id="btn-settings-cancel", color="light", size="sm"),
                dbc.Button("Save Settings", id="btn-settings-save", color="primary", size="sm")
            ], style={"padding": "0.5rem"}),
        ],
        id="settings-modal",
        is_open=False,
        size="md",
        centered=True,
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
                tooltip={"placement": "bottom", "always_visible": False},
                className="p-0 m-0"
            ),
            width=8
        )
    ], className="mb-2 align-items-center")