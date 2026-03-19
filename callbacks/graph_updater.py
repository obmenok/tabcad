import dash
from dash import Input, Output, State, callback, html, dcc
import dash_bootstrap_components as dbc
from core.engine import generate_mesh
from core.renderer import render_tablet
from core.renderer_3d import render_tablet_3d
from core.stl_exporter import generate_tablet_stl
from core.pdf_generator import TabletPDFGenerator
from core.defaults import BASE_DEFAULTS, PROFILE_DEFAULTS, BISECT_DEFAULTS, SHAPE_SPECIFIC


@callback(
    Output("download-pdf", "data"),
    Input("export-pdf-btn", "n_clicks"),
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
        State("input-density", "value"),
    ],
    prevent_initial_call=True,
)
def export_pdf_callback(
    n_clicks,
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
    if not n_clicks:
        return dash.no_update

    try:
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
            density=density,
        )

        mesh_data = generate_mesh(params)
        metrics = mesh_data.get("metrics", {})

        # Generate high-res 2D drawing for PDF with SHADING enabled
        params_2d = dict(params)
        params_2d["render_2d_shaded"] = True
        drawing_2d_b64 = render_tablet(mesh_data, params_2d, dpi=300)

        # Capture 3D view for PDF (Isometric only)
        import base64
        views_3d = []
        for preset in ["Isometric"]:
            p_3d = dict(params)
            p_3d["view_preset"] = preset.lower()
            p_3d["render_mode"] = "shaded"
            p_3d["show_bbox"] = False
            fig_3d = render_tablet_3d(mesh_data, p_3d)

            # Absolute clean layout for export
            fig_3d.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white",
                scene=dict(
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    zaxis=dict(visible=False)
                )
            )
            img_bytes = fig_3d.to_image(format="png", width=500, height=500)
            b64 = f"data:image/png;base64,{base64.b64encode(img_bytes).decode('ascii')}"
            views_3d.append((b64, preset))

        # Generate PDF in a temporary file
        import tempfile
        import os

        # We create a temporary file and close it immediately so PDFGenerator can open it
        fd, temp_pdf_path = tempfile.mkstemp(suffix=".pdf", prefix=f"tablet_specification_{shape}_{profile}_")
        os.close(fd)

        gen = TabletPDFGenerator(temp_pdf_path, params, metrics, drawing_2d_b64=drawing_2d_b64, views_3d=views_3d)
        gen.generate()

        # Define the filename the user will see when downloading
        download_name = f"tablet_specification_{shape}_{profile}.pdf"

        # Send file to user
        data = dcc.send_file(temp_pdf_path, filename=download_name)

        # Note: dcc.send_file will read the file. Dash does not currently have a built-in 
        # automatic cleanup for files sent via send_file, but storing them in the OS temp directory 
        # means the OS will clean them up periodically, keeping our project root clean.
        return data
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        print(f"Error in export_pdf_callback: {e}")
        return dash.no_update


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
    density=None,
    drawing_2d_shaded=False,
    view_preset="isometric",
    show_edges=False,
    show_bbox=False,
):
    return {
        "shape": shape,
        "profile": profile,
        "is_modified": bool(is_mod),
        "W": w if w is not None else BASE_DEFAULTS["W"],
        "L": l if l is not None else BASE_DEFAULTS["L"],
        "Re": re if re is not None else SHAPE_SPECIFIC["oval"]["re"],
        "Rs": rs if rs is not None else SHAPE_SPECIFIC["oval"]["rs"],
        "Dc": dc if dc is not None else BASE_DEFAULTS["dc"],
        "Rc_min": rc_min if rc_min is not None else PROFILE_DEFAULTS["concave"]["rc_min"],
        "Rc_maj": rc_maj if rc_maj is not None else PROFILE_DEFAULTS["concave"]["rc_maj"],
        "Land": land if land is not None else BASE_DEFAULTS["land"],
        "Hb": hb if hb is not None else BASE_DEFAULTS["hb"],
        "Tt": tt if tt is not None else BASE_DEFAULTS["tt"],
        "density": density if density is not None else BASE_DEFAULTS["density"],
        "Bev_D": bev_d if bev_d is not None else PROFILE_DEFAULTS["cbe"]["bev_d"],
        "Bev_A": bev_a if bev_a is not None else PROFILE_DEFAULTS["cbe"]["bev_a"],
        "R_edge": r_edge if r_edge is not None else PROFILE_DEFAULTS["ffre"]["r_edge"],
        "Blend_R": blend_r if blend_r is not None else PROFILE_DEFAULTS["ffbe"]["blend_r"],
        "R_maj_maj": r_maj_maj if r_maj_maj is not None else PROFILE_DEFAULTS["compound"]["r_maj_maj"],
        "R_maj_min": r_maj_min if r_maj_min is not None else PROFILE_DEFAULTS["compound"]["r_maj_min"],
        "R_min_maj": r_min_maj if r_min_maj is not None else PROFILE_DEFAULTS["compound"]["r_min_maj"],
        "R_min_min": r_min_min if r_min_min is not None else PROFILE_DEFAULTS["compound"]["r_min_min"],
        "b_type": b_type if b_type is not None else "none",
        "b_width": b_width if b_width is not None else BISECT_DEFAULTS["standard"]["width"],
        "b_depth": b_depth if b_depth is not None else BISECT_DEFAULTS["standard"]["depth"],
        "b_angle": b_angle if b_angle is not None else BISECT_DEFAULTS["standard"]["angle"],
        "b_Ri": b_ri if b_ri is not None else BISECT_DEFAULTS["standard"]["ri"],
        "b_cruciform": bool(b_cruciform and "on" in b_cruciform),
        "b_double_sided": bool(b_double_sided and "on" in b_double_sided),
        "view_preset": view_preset or "isometric",
        "render_mode": "edges" if bool(show_edges) else "shaded",
        "show_bbox": bool(show_bbox),
        "render_2d_shaded": bool(drawing_2d_shaded),
    }


def _build_calc_html(metrics, density, lang="en"):
    from core.i18n import t
    m = metrics
    tablet_sa = float(m.get("Tablet_SA", 0.0) or 0.0)
    tablet_vol = float(m.get("Tablet_Vol", 0.0) or 0.0)
    tablet_sa_v = (tablet_sa / tablet_vol) if tablet_vol > 1e-12 else 0.0
    density_val = 1.19 if density is None else float(density)
    weight_val = density_val * tablet_vol

    def fmt4(value):
        return f"{float(value):.4f}".replace(".", ",")

    label_style = {"display": "inline-block", "minWidth": "98px"}
    num_style = {
        "display": "inline-block",
        "minWidth": "9ch",
        "textAlign": "right",
        "fontVariantNumeric": "tabular-nums",
    }
    unit_style = {"display": "inline-block"}

    def metric_row(label, value, unit, label_min_width="95px"):
        # Explicit width mapping for each language and column
        if lang == "ru":
            if label_min_width == "95px": label_min_width = "129px"
            elif label_min_width == "107px": label_min_width = "130px"
            elif label_min_width == "99px": label_min_width = "131px"
        elif lang == "cn":
            if label_min_width == "95px": label_min_width = "85px"
            elif label_min_width == "107px": label_min_width = "90px"
            elif label_min_width == "99px": label_min_width = "65px"
            
        return html.Div(
            [
                html.Span([f"{label}:", "\u00a0"], className="calc-label"),
                html.Span(
                    [
                        html.Span(fmt4(value), className="calc-num", style=num_style),
                        html.Span("\u00a0", style={"whiteSpace": "pre"}),
                        html.Span(unit, style=unit_style),
                    ],
                    className="calc-value",
                    style={"whiteSpace": "nowrap"},
                ),
            ],
            className="calc-row",
            style={"--label-width": label_min_width, "marginBottom": "4px"},
        )

    return html.Div(
        [
            html.Div(
                t("calc.title", lang),
                className="fw-bold text-secondary mb-2",
                style={"fontSize": "1rem"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            metric_row(t("calc.die_hole_sa", lang), m.get("Die_Hole_SA", 0), t("units.mm2", lang), label_min_width="95px"),
                            metric_row(t("calc.cup_sa", lang), m.get("Cup_SA", 0), t("units.mm2", lang), label_min_width="95px"),
                            metric_row(t("calc.cup_vol", lang), m.get("Cup_Volume", 0), t("units.mm3", lang), label_min_width="95px"),
                        ],
                        className="calc-col",
                        style={"minWidth": 0},
                    ),
                    html.Div(
                        [
                            metric_row(t("calc.tablet_sa", lang), tablet_sa, t("units.mm2", lang), label_min_width="107px"),
                            metric_row(t("calc.tablet_vol", lang), tablet_vol, t("units.mm3", lang), label_min_width="107px"),
                            metric_row(t("calc.tablet_weight", lang), weight_val, t("units.mg", lang), label_min_width="107px"),
                        ],
                        className="calc-col",
                        style={"minWidth": 0},
                    ),
                    html.Div(
                        [
                            metric_row(t("calc.tablet_density", lang), density_val, t("units.mg_mm3", lang), label_min_width="99px"),
                            metric_row(t("calc.tablet_sa_v", lang), tablet_sa_v, t("units.inv_mm", lang), label_min_width="99px"),
                            metric_row(t("calc.perimeter", lang), m.get("Perimeter", 0), t("units.mm", lang), label_min_width="99px"),
                        ],
                        className="calc-col",
                        style={"minWidth": 0},
                    ),
                ],
                className=f"calc-grid calc-grid-{lang}",
            ),
        ],
        style={"fontSize": "14px"},
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
    if w is None or dc is None or profile is None:
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

    try:
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
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        print(f"Error in generate_graphics: {e}")
        return dash.no_update, dash.no_update



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
        Input("lang-store", "data"),
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
    lang,
):
    if w is None or dc is None or profile is None:
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

    try:
        lang = lang or "en"
        mesh_data = generate_mesh(params)
        return _build_calc_html(mesh_data["metrics"], density, lang)
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        print(f"Error in update_calc_output: {e}")
        return html.Div(
            [
                html.H6("Invalid Geometry", className="text-danger fw-bold"),
                html.P("Current parameters result in impossible geometry. Please check your dimensions.", className="small mb-0")
            ],
            className="p-2 border border-danger rounded bg-light"
        )


@callback(
    Output("download-stl", "data"),
    Input("plotly-stl-btn", "n_clicks"),
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
def export_stl_callback(
    n_clicks,
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
    if n_clicks is None:
        return dash.no_update

    try:
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
        stl_bytes = generate_tablet_stl(mesh_data, params)

        filename = f"tablet_{shape}_{profile}.stl"
        return dcc.send_bytes(stl_bytes, filename)
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        print(f"Error in export_stl_callback: {e}")
        return dash.no_update
