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
    Output("app-settings-store", "data"),
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
        State("set-web-3d-bot-ambient", "value"),
        State("set-web-3d-bot-diffuse", "value"),
        State("set-web-3d-bot-specular", "value"),
        State("set-web-3d-bot-roughness", "value"),
        State("set-web-3d-bot-fresnel", "value"),
        State("set-pdf-orientation", "value"),
        State("set-pdf-2d-fill", "value"),
        State("set-pdf-2d-shaded", "value"),
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
    w3d_bot_amb, w3d_bot_diff, w3d_bot_spec, w3d_bot_rough, w3d_bot_fresnel,
    pdf_ori, pdf_2d_fill, pdf_2d_shaded, pdf_created, pdf_approved,
    current_data
):
    trigger = ctx.triggered_id
    if not trigger:
        return dash.no_update
    
    if trigger == "btn-settings-reset":
        return DEFAULT_APP_SETTINGS
    
    settings = dict(current_data) if current_data else dict(DEFAULT_APP_SETTINGS)
    
    settings["web_2d_fill_color"] = w2d_fill
    settings["web_2d_dim_color"] = w2d_dim
    
    settings["web_3d_model_color"] = w3d_color
    settings["web_3d_lighting_ambient"] = w3d_amb
    settings["web_3d_lighting_diffuse"] = w3d_diff
    settings["web_3d_lighting_specular"] = w3d_spec
    settings["web_3d_lighting_roughness"] = w3d_rough
    settings["web_3d_lighting_fresnel"] = w3d_fresnel

    settings["web_3d_lighting_bot_ambient"] = w3d_bot_amb
    settings["web_3d_lighting_bot_diffuse"] = w3d_bot_diff
    settings["web_3d_lighting_bot_specular"] = w3d_bot_spec
    settings["web_3d_lighting_bot_roughness"] = w3d_bot_rough
    settings["web_3d_lighting_bot_fresnel"] = w3d_bot_fresnel
    
    settings["pdf_orientation"] = pdf_ori
    settings["pdf_2d_fill_color"] = pdf_2d_fill
    settings["pdf_2d_shaded"] = bool(pdf_2d_shaded)
    settings["pdf_created_by"] = pdf_created
    settings["pdf_approved_by"] = pdf_approved
    
    return settings

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
        Output("set-web-3d-bot-ambient", "value"),
        Output("set-web-3d-bot-diffuse", "value"),
        Output("set-web-3d-bot-specular", "value"),
        Output("set-web-3d-bot-roughness", "value"),
        Output("set-web-3d-bot-fresnel", "value"),
        Output("set-pdf-orientation", "value"),
        Output("set-pdf-2d-fill", "value"),
        Output("set-pdf-2d-shaded", "value"),
        Output("set-pdf-created-by", "value"),
        Output("set-pdf-approved-by", "value"),
    ],
    Input("settings-modal", "is_open"),
    State("app-settings-store", "data"),
    prevent_initial_call=True
)
def load_settings_into_modal(is_open, current_data):
    if not is_open:
        return [dash.no_update] * 18
        
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
        s.get("web_3d_lighting_bot_ambient", DEFAULT_APP_SETTINGS["web_3d_lighting_bot_ambient"]),
        s.get("web_3d_lighting_bot_diffuse", DEFAULT_APP_SETTINGS["web_3d_lighting_bot_diffuse"]),
        s.get("web_3d_lighting_bot_specular", DEFAULT_APP_SETTINGS["web_3d_lighting_bot_specular"]),
        s.get("web_3d_lighting_bot_roughness", DEFAULT_APP_SETTINGS["web_3d_lighting_bot_roughness"]),
        s.get("web_3d_lighting_bot_fresnel", DEFAULT_APP_SETTINGS["web_3d_lighting_bot_fresnel"]),
        s.get("pdf_orientation", DEFAULT_APP_SETTINGS["pdf_orientation"]),
        s.get("pdf_2d_fill_color", DEFAULT_APP_SETTINGS["pdf_2d_fill_color"]),
        s.get("pdf_2d_shaded", DEFAULT_APP_SETTINGS["pdf_2d_shaded"]),
        s.get("pdf_created_by", DEFAULT_APP_SETTINGS["pdf_created_by"]),
        s.get("pdf_approved_by", DEFAULT_APP_SETTINGS["pdf_approved_by"]),
    )