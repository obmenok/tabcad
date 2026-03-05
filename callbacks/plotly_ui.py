from dash import Input, Output, clientside_callback


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


clientside_callback(
    """
    function(n) {
        if (!n) {
            return window.dash_clientside.no_update;
        }
        const img = document.getElementById("tablet-drawing");
        if (!img || !img.src) {
            return "drawing-screenshot:image_not_found";
        }
        try {
            const a = document.createElement("a");
            a.href = img.src;
            a.download = "tabletcad-2d.png";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            return "drawing-screenshot:ok:" + String(n);
        } catch (e) {
            return "drawing-screenshot:error";
        }
    }
    """,
    Output("drawing-screenshot-signal", "children"),
    Input("drawing-screenshot-btn", "n_clicks"),
    prevent_initial_call=True,
)
