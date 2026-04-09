import dash
from dash import Input, Output, State, callback, ctx
import json
from core.defaults import DEFAULT_APP_SETTINGS

@callback(
    Output("settings-modal", "is_open"),
    [
        Input("btn-open-settings", "n_clicks"),
        Input("btn-settings-cancel", "n_clicks"),
        Input("btn-settings-save", "n_clicks"),
    ],
    State("settings-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_settings_modal(n_open, n_cancel, n_save, is_open):
    if not ctx.triggered_id:
        return dash.no_update
    return not is_open

@callback(
    [Output("app-settings-store", "data")] + 
    [Output(f"set-{k}", "value", allow_duplicate=True) for k in [
        "web-2d-fill", "web-2d-dim", "web-3d-model-color",
        "web-3d-ambient", "web-3d-diffuse", "web-3d-specular", "web-3d-roughness", "web-3d-fresnel",
        "pdf-orientation", "pdf-2d-fill", "pdf-dim-font-size", "pdf-2d-shaded", "pdf-include-3d", "pdf-created-by", "pdf-approved-by",
    ]],
    [
        Input("btn-settings-save", "n_clicks"),
        Input("btn-settings-reset", "n_clicks"),
    ],
    [
        State("set-web-2d-fill", "value"),
        State("set-web-2d-dim", "value"),
        State("set-web-3d-model-color", "value"),
        State("set-web-3d-ambient", "value"),
        State("set-web-3d-diffuse", "value"),
        State("set-web-3d-specular", "value"),
        State("set-web-3d-roughness", "value"),
        State("set-web-3d-fresnel", "value"),
        State("set-pdf-orientation", "value"),
        State("set-pdf-2d-fill", "value"),
        State("set-pdf-dim-font-size", "value"),
        State("set-pdf-2d-shaded", "value"),
        State("set-pdf-include-3d", "value"),
        State("set-pdf-created-by", "value"),
        State("set-pdf-approved-by", "value"),
        State("app-settings-store", "data"),
    ],
    prevent_initial_call=True
)
def save_settings(
    n_save, n_reset,
    w2d_fill, w2d_dim,
    w3d_color, w3d_amb, w3d_diff, w3d_spec, w3d_rough, w3d_fresnel,
    pdf_ori, pdf_2d_fill, pdf_dim_font_size, pdf_2d_shaded, pdf_include_3d, pdf_created, pdf_approved,
    current_data
):
    trigger = ctx.triggered_id
    if not trigger:
        return [dash.no_update] * 16
    
    if trigger == "btn-settings-reset":
        return [DEFAULT_APP_SETTINGS] + [
            DEFAULT_APP_SETTINGS["web_2d_fill_color"],
            DEFAULT_APP_SETTINGS["web_2d_dim_color"],
            DEFAULT_APP_SETTINGS["web_3d_model_color"],
            DEFAULT_APP_SETTINGS["web_3d_lighting_ambient"],
            DEFAULT_APP_SETTINGS["web_3d_lighting_diffuse"],
            DEFAULT_APP_SETTINGS["web_3d_lighting_specular"],
            DEFAULT_APP_SETTINGS["web_3d_lighting_roughness"],
            DEFAULT_APP_SETTINGS["web_3d_lighting_fresnel"],
            DEFAULT_APP_SETTINGS["pdf_orientation"],
            DEFAULT_APP_SETTINGS["pdf_2d_fill_color"],
            DEFAULT_APP_SETTINGS["pdf_2d_dim_font_size"],
            DEFAULT_APP_SETTINGS["pdf_2d_shaded"],
            DEFAULT_APP_SETTINGS["pdf_include_3d"],
            DEFAULT_APP_SETTINGS["pdf_created_by"],
            DEFAULT_APP_SETTINGS["pdf_approved_by"],
        ]
    
    # Save button: only update store, not fields
    settings = dict(current_data) if current_data else dict(DEFAULT_APP_SETTINGS)
    
    settings["web_2d_fill_color"] = w2d_fill
    settings["web_2d_dim_color"] = w2d_dim
    
    settings["web_3d_model_color"] = w3d_color
    settings["web_3d_lighting_ambient"] = w3d_amb
    settings["web_3d_lighting_diffuse"] = w3d_diff
    settings["web_3d_lighting_specular"] = w3d_spec
    settings["web_3d_lighting_roughness"] = w3d_rough
    settings["web_3d_lighting_fresnel"] = w3d_fresnel

    # Remove legacy bot lighting settings if they exist
    for key in list(settings.keys()):
        if key.startswith("web_3d_lighting_bot_"):
            del settings[key]
    
    settings["pdf_orientation"] = pdf_ori
    settings["pdf_2d_fill_color"] = pdf_2d_fill
    settings["pdf_2d_dim_font_size"] = int(pdf_dim_font_size) if pdf_dim_font_size else 8
    settings["pdf_2d_shaded"] = bool(pdf_2d_shaded)
    settings["pdf_include_3d"] = bool(pdf_include_3d)
    settings["pdf_created_by"] = pdf_created
    settings["pdf_approved_by"] = pdf_approved
    
    # Return store + no_update for all field outputs (only store is updated on save)
    return [settings] + [dash.no_update] * 15

@callback(
    [
        Output("set-web-2d-fill", "value"),
        Output("set-web-2d-dim", "value"),
        Output("set-web-3d-model-color", "value"),
        Output("set-web-3d-ambient", "value"),
        Output("set-web-3d-diffuse", "value"),
        Output("set-web-3d-specular", "value"),
        Output("set-web-3d-roughness", "value"),
        Output("set-web-3d-fresnel", "value"),
        Output("set-pdf-orientation", "value"),
        Output("set-pdf-2d-fill", "value"),
        Output("set-pdf-dim-font-size", "value"),
        Output("set-pdf-2d-shaded", "value"),
        Output("set-pdf-include-3d", "value"),
        Output("set-pdf-created-by", "value"),
        Output("set-pdf-approved-by", "value"),
    ],
    Input("settings-modal", "is_open"),
    State("app-settings-store", "data"),
    prevent_initial_call=True
)
def load_settings_into_modal(is_open, current_data):
    if not is_open:
        return [dash.no_update] * 15
        
    s = current_data if current_data else DEFAULT_APP_SETTINGS
    return (
        s.get("web_2d_fill_color", DEFAULT_APP_SETTINGS["web_2d_fill_color"]),
        s.get("web_2d_dim_color", DEFAULT_APP_SETTINGS["web_2d_dim_color"]),
        s.get("web_3d_model_color", DEFAULT_APP_SETTINGS["web_3d_model_color"]),
        s.get("web_3d_lighting_ambient", DEFAULT_APP_SETTINGS["web_3d_lighting_ambient"]),
        s.get("web_3d_lighting_diffuse", DEFAULT_APP_SETTINGS["web_3d_lighting_diffuse"]),
        s.get("web_3d_lighting_specular", DEFAULT_APP_SETTINGS["web_3d_lighting_specular"]),
        s.get("web_3d_lighting_roughness", DEFAULT_APP_SETTINGS["web_3d_lighting_roughness"]),
        s.get("web_3d_lighting_fresnel", DEFAULT_APP_SETTINGS["web_3d_lighting_fresnel"]),
        s.get("pdf_orientation", DEFAULT_APP_SETTINGS["pdf_orientation"]),
        s.get("pdf_2d_fill_color", DEFAULT_APP_SETTINGS["pdf_2d_fill_color"]),
        s.get("pdf_2d_dim_font_size", DEFAULT_APP_SETTINGS["pdf_2d_dim_font_size"]),
        s.get("pdf_2d_shaded", DEFAULT_APP_SETTINGS["pdf_2d_shaded"]),
        s.get("pdf_include_3d", DEFAULT_APP_SETTINGS["pdf_include_3d"]),
        s.get("pdf_created_by", DEFAULT_APP_SETTINGS["pdf_created_by"]),
        s.get("pdf_approved_by", DEFAULT_APP_SETTINGS["pdf_approved_by"]),
    )
