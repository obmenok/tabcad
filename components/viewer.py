from dash import html, dcc
import dash_bootstrap_components as dbc


def create_viewer():
    return html.Div(
        [
            html.Div(id="calc-output", className="mb-3 p-3 bg-light border rounded", style={"minHeight": "80px"}),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    [
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
                                                    html.Span(className="apollo-icon av-i-screenshot"),
                                                    id="drawing-screenshot-btn",
                                                    color="light",
                                                    class_name="plotly-toolbar-btn",
                                                    title="Screenshot",
                                                ),
                                            ],
                                            size="sm",
                                            className="plotly-toolbar-group",
                                        ),
                                    ],
                                    className="d-flex flex-nowrap align-items-center gap-2 plotly-toolbar-wrap",
                                    style={
                                        "position": "absolute",
                                        "top": "8px",
                                        "left": "8px",
                                        "right": "8px",
                                        "zIndex": 5000,
                                        "background": "rgba(255,255,255,0.92)",
                                        "borderRadius": "6px",
                                        "padding": "6px",
                                        "overflow": "visible",
                                    },
                                ),
                                html.Img(
                                    id="tablet-drawing",
                                    src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==",
                                    style={"width": "100%", "height": "100%", "object-fit": "contain"},
                                ),
                                dcc.Store(id="drawing-2d-shaded", data=False),
                                html.Div(id="drawing-fullscreen-signal", style={"display": "none"}),
                                html.Div(id="drawing-screenshot-signal", style={"display": "none"}),
                            ],
                            id="drawing-viewport-panel",
                            className="d-flex justify-content-center align-items-center border rounded bg-white p-2",
                            style={"height": "80vh", "position": "relative"},
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    [
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
                                                            html.Span([html.Span(className="apollo-icon av-i-front av-menu-icon"), "Front"]),
                                                            id="plotly-view-front",
                                                        ),
                                                        dbc.DropdownMenuItem(
                                                            html.Span([html.Span(className="apollo-icon av-i-back av-menu-icon"), "Back"]),
                                                            id="plotly-view-back",
                                                        ),
                                                        dbc.DropdownMenuItem(
                                                            html.Span([html.Span(className="apollo-icon av-i-left av-menu-icon"), "Left"]),
                                                            id="plotly-view-left",
                                                        ),
                                                        dbc.DropdownMenuItem(
                                                            html.Span([html.Span(className="apollo-icon av-i-right av-menu-icon"), "Right"]),
                                                            id="plotly-view-right",
                                                        ),
                                                        dbc.DropdownMenuItem(
                                                            html.Span([html.Span(className="apollo-icon av-i-top av-menu-icon"), "Top"]),
                                                            id="plotly-view-top",
                                                        ),
                                                        dbc.DropdownMenuItem(
                                                            html.Span([html.Span(className="apollo-icon av-i-bottom av-menu-icon"), "Bottom"]),
                                                            id="plotly-view-bottom",
                                                        ),
                                                        dbc.DropdownMenuItem(
                                                            html.Span([html.Span(className="apollo-icon av-i-isometric av-menu-icon"), "Isometric"]),
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
                                                    html.Span(className="apollo-icon av-i-screenshot"),
                                                    id="plotly-screenshot-btn",
                                                    color="light",
                                                    class_name="plotly-toolbar-btn",
                                                    title="Screenshot",
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
                                    ],
                                    className="d-flex flex-nowrap align-items-center gap-2 plotly-toolbar-wrap",
                                    style={
                                        "position": "absolute",
                                        "top": "8px",
                                        "left": "8px",
                                        "right": "8px",
                                        "zIndex": 5000,
                                        "background": "rgba(255,255,255,0.92)",
                                        "borderRadius": "6px",
                                        "padding": "6px",
                                    },
                                ),
                                html.Div(id="tablet-3d", style={"height": "100%"}),
                                dcc.Store(id="plotly-view-preset", data="isometric"),
                                dcc.Store(id="plotly-show-edges", data=False),
                                dcc.Store(id="plotly-show-bbox", data=False),
                                html.Div(id="plotly-fullscreen-signal", style={"display": "none"}),
                                html.Div(id="plotly-screenshot-signal", style={"display": "none"}),
                                dcc.Download(id="download-stl"),
                            ],
                            id="plotly-viewport-panel",
                            className="border rounded bg-white p-2",
                            style={"height": "80vh", "position": "relative", "overflow": "visible"},
                        ),
                        width=6,
                    ),
                ],
                className="g-2",
            ),
        ]
    )
