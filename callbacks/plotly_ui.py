import dash
import base64
from urllib.parse import unquote

from dash import Input, Output, State, callback, clientside_callback, ctx, dcc


clientside_callback(
    """
    function(n) {
        if (!n) {
            return window.dash_clientside.no_update;
        }
        const panel = document.querySelector("#plotly-viewport-panel");
        if (!panel) {
            return "fullscreen:panel_not_found";
        }
        if (!document.fullscreenElement) {
            panel.requestFullscreen();
            return "fullscreen:on:" + String(n);
        }
        document.exitFullscreen();
        return "fullscreen:off:" + String(n);
    }
    """,
    Output("plotly-fullscreen-signal", "children"),
    Input("plotly-fullscreen-btn", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("plotly-view-preset", "data"),
    [
        Input("plotly-view-front", "n_clicks"),
        Input("plotly-view-back", "n_clicks"),
        Input("plotly-view-left", "n_clicks"),
        Input("plotly-view-right", "n_clicks"),
        Input("plotly-view-top", "n_clicks"),
        Input("plotly-view-bottom", "n_clicks"),
        Input("plotly-view-isometric", "n_clicks"),
    ],
    State("plotly-view-preset", "data"),
    prevent_initial_call=True,
)
def select_view_preset(_, __, ___, ____, _____, ______, _______, current):
    mapping = {
        "plotly-view-front": "front",
        "plotly-view-back": "back",
        "plotly-view-left": "left",
        "plotly-view-right": "right",
        "plotly-view-top": "top",
        "plotly-view-bottom": "bottom",
        "plotly-view-isometric": "isometric",
    }
    trig = ctx.triggered_id
    return mapping.get(trig, current or "isometric")


@callback(
    [
        Output("plotly-show-edges", "data"),
        Output("plotly-edge-btn", "style"),
        Output("plotly-show-bbox", "data"),
        Output("plotly-bbox-btn", "style"),
    ],
    [Input("plotly-edge-btn", "n_clicks"), Input("plotly-bbox-btn", "n_clicks")],
    [State("plotly-show-edges", "data"), State("plotly-show-bbox", "data")],
    prevent_initial_call=True,
)
def toggle_plotly_modes(edge_clicks, bbox_clicks, edge_on, bbox_on):
    trig = ctx.triggered_id
    edge_on = bool(edge_on)
    bbox_on = bool(bbox_on)
    if trig == "plotly-edge-btn":
        edge_on = not edge_on
    elif trig == "plotly-bbox-btn":
        bbox_on = not bbox_on

    def _btn_style(active):
        if active:
            return {
                "backgroundColor": "#e9ecef",
                "borderColor": "#6c757d",
                "color": "#212529",
            }
        return {
            "backgroundColor": "#ffffff",
            "borderColor": "#9aa0a6",
            "color": "#495057",
        }

    return edge_on, _btn_style(edge_on), bbox_on, _btn_style(bbox_on)


@callback(
    [Output("drawing-2d-shaded", "data"), Output("drawing-shaded-btn", "style")],
    Input("drawing-shaded-btn", "n_clicks"),
    State("drawing-2d-shaded", "data"),
    prevent_initial_call=True,
)
def toggle_drawing_shaded(_, shaded_on):
    shaded_on = not bool(shaded_on)
    if shaded_on:
        style = {
            "backgroundColor": "#e9ecef",
            "borderColor": "#6c757d",
            "color": "#212529",
        }
    else:
        style = {
            "backgroundColor": "#ffffff",
            "borderColor": "#9aa0a6",
            "color": "#495057",
        }
    return shaded_on, style


clientside_callback(
    """
    function(n) {
        if (!n) {
            return window.dash_clientside.no_update;
        }
        const gd = document.querySelector("#tablet-3d-graph .js-plotly-plot");
        if (!gd || !window.Plotly) {
            return "screenshot:plot_not_found";
        }
        try {
            window.Plotly.downloadImage(gd, {
                format: "png",
                filename: "tabletcad-3d",
                width: Math.max(1200, gd.clientWidth || 1200),
                height: Math.max(900, gd.clientHeight || 900),
                scale: 2
            });
            return "screenshot:ok:" + String(n);
        } catch (e) {
            return "screenshot:error";
        }
    }
    """,
    Output("plotly-screenshot-signal", "children"),
    Input("plotly-screenshot-btn", "n_clicks"),
    prevent_initial_call=True,
)


clientside_callback(
    """
    function(n) {
        if (!n) {
            return window.dash_clientside.no_update;
        }
        const panel = document.querySelector("#drawing-viewport-panel");
        if (!panel) {
            return "drawing-fullscreen:panel_not_found";
        }
        if (!document.fullscreenElement) {
            panel.requestFullscreen();
            return "drawing-fullscreen:on:" + String(n);
        }
        document.exitFullscreen();
        return "drawing-fullscreen:off:" + String(n);
    }
    """,
    Output("drawing-fullscreen-signal", "children"),
    Input("drawing-fullscreen-btn", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("download-2d", "data"),
    Input("drawing-download-png-btn", "n_clicks"),
    Input("drawing-download-svg-btn", "n_clicks"),
    State("tablet-drawing", "src"),
    State("drawing-2d-png-src", "data"),
    prevent_initial_call=True,
)
def download_2d_screenshot(png_clicks, svg_clicks, svg_src, png_src):
    trig = ctx.triggered_id
    img_src = png_src if trig == "drawing-download-png-btn" else svg_src
    if not img_src or not img_src.startswith("data:"):
        return dash.no_update

    try:
        header, payload = img_src.split(",", 1)
    except ValueError:
        return dash.no_update

    is_base64 = ";base64" in header
    mime = header[5:].split(";")[0]

    if trig == "drawing-download-svg-btn" and mime == "image/svg+xml":
        filename = "tabletcad-2d.svg"
        if is_base64:
            content = base64.b64decode(payload).decode("utf-8")
        else:
            content = unquote(payload)
        return dict(content=content, filename=filename, type=mime)

    if trig == "drawing-download-png-btn" and mime == "image/png":
        filename = "tabletcad-2d.png"
        if not is_base64:
            return dash.no_update
        return dcc.send_bytes(lambda buffer: buffer.write(base64.b64decode(payload)), filename)

    return dash.no_update
