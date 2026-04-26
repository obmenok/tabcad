import dash

from dash import Input, Output, State, callback, clientside_callback, ctx


clientside_callback(
    """
    function(n) {
        if (!n) {
            return window.dash_clientside.no_update;
        }
        const panel = document.querySelector("#viewer-viewport-panel");
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
    [
        Output("viewer-mode-store", "data"),
        Output("viewer-mode-2d-btn", "class_name"),
        Output("viewer-mode-3d-btn", "class_name"),
    ],
    [
        Input("viewer-mode-2d-btn", "n_clicks"),
        Input("viewer-mode-3d-btn", "n_clicks"),
    ],
    State("viewer-mode-store", "data"),
    prevent_initial_call=True,
)
def set_viewer_mode(_, __, current_mode):
    trig = ctx.triggered_id
    if trig == "viewer-mode-3d-btn":
        mode = "3d"
    elif trig == "viewer-mode-2d-btn":
        mode = "2d"
    else:
        mode = current_mode or "2d"

    class_2d = "plotly-toolbar-btn active" if mode == "2d" else "plotly-toolbar-btn"
    class_3d = "plotly-toolbar-btn active" if mode == "3d" else "plotly-toolbar-btn"
    return mode, class_2d, class_3d


@callback(
    [
        Output("viewer-2d-layer", "style"),
        Output("viewer-3d-layer", "style"),
        Output("viewer-toolbar-2d", "style"),
        Output("viewer-toolbar-3d", "style"),
    ],
    Input("viewer-mode-store", "data"),
    prevent_initial_call=False,
)
def toggle_viewer_mode_layout(mode):
    base_layer = {"height": "100%", "width": "100%"}
    toolbar_base = {
        "position": "absolute",
        "top": "8px",
        "right": "8px",
        "zIndex": 5000,
        "background": "rgba(255,255,255,0.92)",
        "borderRadius": "6px",
        "padding": "6px",
        "overflow": "visible",
    }
    if mode == "3d":
        layer_2d = {**base_layer, "display": "none"}
        layer_3d = {**base_layer, "display": "block"}
        toolbar_2d = {**toolbar_base, "display": "none"}
        toolbar_3d = {**toolbar_base, "display": "flex"}
        return layer_2d, layer_3d, toolbar_2d, toolbar_3d

    layer_2d = {**base_layer, "display": "block"}
    layer_3d = {**base_layer, "display": "none"}
    toolbar_2d = {**toolbar_base, "display": "flex"}
    toolbar_3d = {**toolbar_base, "display": "none"}
    return layer_2d, layer_3d, toolbar_2d, toolbar_3d


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
        const panel = document.querySelector("#viewer-viewport-panel");
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
