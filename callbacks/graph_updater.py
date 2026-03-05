import dash
from dash import Input, Output, State, callback, html, dcc
import dash_bootstrap_components as dbc
from core.engine import generate_mesh
from core.renderer import render_tablet
from core.renderer_3d import render_tablet_3d


@callback(
    [
        Output("tablet-drawing", "src"),
        Output("calc-output", "children"),
        Output("tablet-3d", "children"),
    ],
    [
        Input("btn-generate", "n_clicks"),
        Input("drawing-2d-shaded", "data"),
        Input("plotly-view-preset", "data"),
        Input("plotly-show-edges", "data"),
        Input("plotly-show-bbox", "data"),
    ],
    [
        State("shape-dropdown", "value"),
        State("profile-dropdown", "value"),
        State("modified-switch", "value"),
        State("input-w", "value"),
        State("input-l", "value"),
        State("input-re", "value"),
        State("input-rs", "value"),
        State("input-dc", "value"),
        State("input-rc-min", "value"),
        State("input-rc-maj", "value"),
        State("input-land", "value"),
        State("input-hb", "value"),
        State("input-tt", "value"),
        State("input-bev-d", "value"),
        State("input-bev-a", "value"),
        State("input-r-edge", "value"),
        State("input-blend-r", "value"),
        State("input-r-maj-maj", "value"),
        State("input-r-maj-min", "value"),
        State("input-r-min-maj", "value"),
        State("input-r-min-min", "value"),
        State("bisect-type", "value"),
        State("input-b-width", "value"),
        State("input-b-depth", "value"),
        State("input-b-angle", "value"),
        State("input-b-ri", "value"),
        State("bisect-cruciform", "value"),
        State("bisect-double-sided", "value"),
    ],
    prevent_initial_call=True,
)
def generate_graphics(
    n_clicks,
    drawing_2d_shaded,
    view_preset,
    show_edges,
    show_bbox,
    shape,
    profile,
    is_mod,
    w,
    l,
    re,
    rs,
    dc,
    rc_min,
    rc_maj,
    land,
    hb,
    tt,
    bev_d,
    bev_a,
    r_edge,
    blend_r,
    r_maj_maj,
    r_maj_min,
    r_min_maj,
    r_min_min,
    b_type,
    b_width,
    b_depth,
    b_angle,
    b_ri,
    b_cruciform,
    b_double_sided,
):
    if w is None or dc is None:
        return dash.no_update, html.Div("Please enter valid dimensions", className="text-danger"), dash.no_update

    params = {
        "shape": shape,
        "profile": profile,
        "is_modified": bool(is_mod),
        "W": w,
        "L": l,
        "Re": re,
        "Rs": rs,
        "Dc": dc,
        "Rc_min": rc_min,
        "Rc_maj": rc_maj,
        "Land": land,
        "Hb": hb,
        "Tt": tt,
        "Bev_D": bev_d,
        "Bev_A": bev_a,
        "R_edge": r_edge,
        "Blend_R": blend_r,
        "R_maj_maj": r_maj_maj,
        "R_maj_min": r_maj_min,
        "R_min_maj": r_min_maj,
        "R_min_min": r_min_min,
        "b_type": b_type,
        "b_width": b_width,
        "b_depth": b_depth,
        "b_angle": b_angle,
        "b_Ri": b_ri,
        "b_cruciform": bool(b_cruciform and "on" in b_cruciform),
        "b_double_sided": bool(b_double_sided and "on" in b_double_sided),
        "view_preset": view_preset or "isometric",
        "render_mode": "edges" if bool(show_edges) else "shaded",
        "show_bbox": bool(show_bbox),
        "render_2d_shaded": bool(drawing_2d_shaded),
    }

    mesh_data = generate_mesh(params)
    img_src = render_tablet(mesh_data, params)
    fig = render_tablet_3d(mesh_data, params)
    fig_3d = dcc.Graph(
        figure=fig,
        style={"height": "100%", "width": "100%"},
        config={"displaylogo": False, "displayModeBar": False, "responsive": True},
        id="tablet-3d-graph",
    )

    m = mesh_data["metrics"]
    calc_html = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(html.Div([html.Strong("Die Hole SA: "), html.Span(f"{m.get('Die_Hole_SA', 0):.4f} mm2")])),
                    dbc.Col(html.Div([html.Strong("Perimeter: "), html.Span(f"{m.get('Perimeter', 0):.4f} mm")])),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div([html.Strong("Cup Volume: "), html.Span(f"{m.get('Cup_Volume', 0):.4f} mm3")])),
                    dbc.Col(html.Div([html.Strong("Tablet SA: "), html.Span(f"{m.get('Tablet_SA', 0):.4f} mm2")])),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div([html.Strong("Cup SA: "), html.Span(f"{m.get('Cup_SA', 0):.4f} mm2")])),
                    dbc.Col(html.Div([html.Strong("Tablet Vol: "), html.Span(f"{m.get('Tablet_Vol', 0):.4f} mm3")])),
                ]
            ),
        ]
    )

    return img_src, calc_html, fig_3d
