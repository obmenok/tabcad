import dash
from dash import Input, Output, State, callback, html, dcc
import dash_bootstrap_components as dbc
from core.engine import generate_mesh
from core.renderer import render_tablet
from core.renderer_3d import render_tablet_3d


def _build_params(
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
    drawing_2d_shaded=False,
    view_preset="isometric",
    show_edges=False,
    show_bbox=False,
):
    return {
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


def _build_calc_html(metrics, density):
    m = metrics
    tablet_sa = float(m.get("Tablet_SA", 0.0) or 0.0)
    tablet_vol = float(m.get("Tablet_Vol", 0.0) or 0.0)
    tablet_sa_v = (tablet_sa / tablet_vol) if tablet_vol > 1e-12 else 0.0
    density_val = 1.19 if density is None else float(density)
    weight_val = density_val * tablet_vol

    def fmt4(value):
        return f"{float(value):.4f}".replace(".", ",")

    label_style = {"display": "inline-block", "minWidth": "112px"}
    num_style = {
        "fontFamily": "Consolas, 'Courier New', monospace",
        "display": "inline-block",
        "minWidth": "8ch",
        "textAlign": "right",
    }
    unit_style = {"display": "inline-block", "minWidth": "6ch"}

    def metric_row(label, value, unit, label_min_width="112px"):
        row_label_style = dict(label_style)
        row_label_style["minWidth"] = label_min_width
        return html.Div(
            [
                html.Span([f"{label}:", "\u00a0"], style=row_label_style),
                html.Span(
                    [
                        html.Span(fmt4(value), style=num_style),
                        html.Span("\u00a0", style={"whiteSpace": "pre"}),
                        html.Span(unit, style=unit_style),
                    ],
                    style={"whiteSpace": "nowrap"},
                ),
            ],
            className="d-flex flex-column flex-xl-row align-items-start align-items-xl-center mb-1",
            style={"columnGap": "2px", "rowGap": "1px"},
        )

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                metric_row("Die Hole SA", m.get("Die_Hole_SA", 0), "mm\u00b2", label_min_width="98px"),
                                metric_row("Cup SA", m.get("Cup_SA", 0), "mm\u00b2", label_min_width="98px"),
                                metric_row("Cup Volume", m.get("Cup_Volume", 0), "mm\u00b3", label_min_width="98px"),
                            ]
                        ),
                        width=4,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                metric_row("Tablet SA", tablet_sa, "mm\u00b2", label_min_width="118px"),
                                metric_row("Tablet Volume", tablet_vol, "mm\u00b3", label_min_width="118px"),
                                metric_row("Tablet Weight", weight_val, "mg", label_min_width="118px"),
                            ]
                        ),
                        width=4,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                metric_row("Tablet Density", density_val, "mg/mm\u00b3", label_min_width="102px"),
                                metric_row("Tablet SA/V", tablet_sa_v, "1/mm", label_min_width="102px"),
                                metric_row("Perimeter", m.get("Perimeter", 0), "mm", label_min_width="102px"),
                            ]
                        ),
                        width=4,
                    ),
                ]
            ),
        ]
    )


@callback(
    [
        Output("tablet-drawing", "src"),
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
        return dash.no_update, dash.no_update

    params = _build_params(
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
        drawing_2d_shaded=drawing_2d_shaded,
        view_preset=view_preset,
        show_edges=show_edges,
        show_bbox=show_bbox,
    )

    mesh_data = generate_mesh(params)
    img_src = render_tablet(mesh_data, params)
    fig = render_tablet_3d(mesh_data, params)
    fig_3d = dcc.Graph(
        figure=fig,
        style={"height": "100%", "width": "100%"},
        config={"displaylogo": False, "displayModeBar": False, "responsive": True},
        id="tablet-3d-graph",
    )

    return img_src, fig_3d


@callback(
    Output("calc-output", "children"),
    [
        Input("shape-dropdown", "value"),
        Input("profile-dropdown", "value"),
        Input("modified-switch", "value"),
        Input("input-w", "value"),
        Input("input-l", "value"),
        Input("input-re", "value"),
        Input("input-rs", "value"),
        Input("input-dc", "value"),
        Input("input-rc-min", "value"),
        Input("input-rc-maj", "value"),
        Input("input-land", "value"),
        Input("input-hb", "value"),
        Input("input-tt", "value"),
        Input("input-bev-d", "value"),
        Input("input-bev-a", "value"),
        Input("input-r-edge", "value"),
        Input("input-blend-r", "value"),
        Input("input-r-maj-maj", "value"),
        Input("input-r-maj-min", "value"),
        Input("input-r-min-maj", "value"),
        Input("input-r-min-min", "value"),
        Input("bisect-type", "value"),
        Input("input-b-width", "value"),
        Input("input-b-depth", "value"),
        Input("input-b-angle", "value"),
        Input("input-b-ri", "value"),
        Input("bisect-cruciform", "value"),
        Input("bisect-double-sided", "value"),
        Input("input-density", "value"),
    ],
    prevent_initial_call=False,
)
def update_calc_panel_live(
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
    density,
):
    if w is None or dc is None:
        return html.Div("Please enter valid dimensions", className="text-danger")

    params = _build_params(
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
    )

    mesh_data = generate_mesh(params)
    return _build_calc_html(mesh_data["metrics"], density)
