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
                            html.Img(
                                id="tablet-drawing",
                                style={"width": "100%", "max-height": "80vh", "object-fit": "contain"},
                            ),
                            className="d-flex justify-content-center align-items-center border rounded bg-white",
                            style={"height": "80vh"},
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dbc.Button("Fullscreen", id="plotly-fullscreen-btn", size="sm", color="secondary", outline=True),
                                        dbc.Button("Screenshot", id="plotly-screenshot-btn", size="sm", color="secondary", outline=True),
                                        html.Div(
                                            dcc.Dropdown(
                                                id="plotly-view-preset",
                                                options=[
                                                    {"label": "Isometric", "value": "isometric"},
                                                    {"label": "Front", "value": "front"},
                                                    {"label": "Back", "value": "back"},
                                                    {"label": "Left", "value": "left"},
                                                    {"label": "Right", "value": "right"},
                                                    {"label": "Top", "value": "top"},
                                                    {"label": "Bottom", "value": "bottom"},
                                                ],
                                                value="isometric",
                                                clearable=False,
                                                searchable=False,
                                            ),
                                            style={"minWidth": "180px", "maxWidth": "220px", "flex": "1 0 auto"},
                                        ),
                                        dbc.Checklist(
                                            id="plotly-show-edges",
                                            options=[{"label": "Edge", "value": "on"}],
                                            value=[],
                                            switch=True,
                                        ),
                                        dbc.Checklist(
                                            id="plotly-show-bbox",
                                            options=[{"label": "Boundary Box", "value": "on"}],
                                            value=[],
                                            switch=True,
                                        ),
                                    ],
                                    className="d-flex flex-nowrap align-items-center gap-2 mb-2",
                                ),
                                html.Div(id="tablet-3d", style={"height": "74vh"}),
                                html.Div(id="plotly-fullscreen-signal", style={"display": "none"}),
                                html.Div(id="plotly-screenshot-signal", style={"display": "none"}),
                            ],
                            id="plotly-viewport-panel",
                            className="border rounded bg-white p-2",
                            style={"height": "80vh"},
                        ),
                        width=6,
                    ),
                ],
                className="g-2",
            ),
        ]
    )
