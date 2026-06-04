import dash
from dash import Input, Output, State, callback, ctx
import json
from core.defaults import DEFAULT_APP_SETTINGS

@callback(
    Output("app-settings-store", "data"),
    [
        Input("set-web-2d-fill", "value"),
        Input("set-web-2d-dim", "value"),
        Input("set-web-3d-model-color", "value"),
        Input("set-web-3d-ambient", "value"),
        Input("set-web-3d-diffuse", "value"),
        Input("set-web-3d-specular", "value"),
        Input("set-web-3d-roughness", "value"),
        Input("set-web-3d-fresnel", "value"),
        Input("set-pdf-orientation", "value"),
        Input("set-pdf-2d-fill", "value"),
        Input("set-pdf-dim-font-size", "value"),
        Input("set-pdf-2d-shaded", "value"),
        Input("set-pdf-include-3d", "value"),
        Input("set-pdf-3d-quality", "value"),
        Input("set-pdf-created-by", "value"),
        Input("set-pdf-approved-by", "value"),
    ],
    State("app-settings-store", "data"),
    prevent_initial_call=True
)
def update_settings_store(
    w2d_fill, w2d_dim,
    w3d_color, w3d_amb, w3d_diff, w3d_spec, w3d_rough, w3d_fresnel,
    pdf_ori, pdf_2d_fill, pdf_dim_font_size, pdf_2d_shaded, pdf_include_3d, pdf_3d_quality, pdf_created, pdf_approved,
    current_data
):
    trigger = ctx.triggered_id
    if not trigger:
        return dash.no_update
    
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
    settings["pdf_3d_quality"] = pdf_3d_quality
    settings["pdf_created_by"] = pdf_created
    settings["pdf_approved_by"] = pdf_approved
    
    if current_data and settings == current_data:
        return dash.no_update
        
    return settings

# Update the inputs when reset is clicked
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
        Output("set-pdf-3d-quality", "value"),
        Output("set-pdf-created-by", "value"),
        Output("set-pdf-approved-by", "value"),
    ],
    Input("btn-settings-reset", "n_clicks"),
    prevent_initial_call=True
)
def reset_settings_inputs(n_clicks):
    if not n_clicks:
        return [dash.no_update] * 16

    return (
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
        DEFAULT_APP_SETTINGS["pdf_3d_quality"],
        DEFAULT_APP_SETTINGS["pdf_created_by"],
        DEFAULT_APP_SETTINGS["pdf_approved_by"],
    )
