from dash import dcc, html
import dash_bootstrap_components as dbc


def create_viewer():
    return html.Div(
        [
            html.Div(id="calc-output", className="mb-3 p-3 bg-light border rounded", style={"minHeight": "80px"}),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            html.Img(id="tablet-drawing", style={"width": "100%", "max-height": "80vh", "object-fit": "contain"}),
                            className="d-flex justify-content-center align-items-center border rounded bg-white",
                            style={"height": "80vh"},
                        ),
                        width=6, #раньше было 8
                    ),
                    dbc.Col(
                        html.Div(
                            dcc.Graph(
                                id="tablet-3d",
                                style={"height": "80vh"},
                                config={"displaylogo": False, "responsive": True},
                            ),
                            className="border rounded bg-white",
                            style={"height": "80vh"},
                        ),
                        width=6, #раньше было 4
                    ),
                ],
                className="g-2",
            ),
        ]
    )
