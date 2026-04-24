import dash
import numpy as np
from dash import Input, Output, State, callback, ctx
from core.defaults import BASE_DEFAULTS, PROFILE_DEFAULTS, BISECT_DEFAULTS, SHAPE_SPECIFIC
from core.tip_force import calculate_tip_force


@callback(
    [
        Output("shape-dropdown", "value"),
        Output("profile-dropdown", "value", allow_duplicate=True),
        Output("shape-round-btn", "class_name"),
        Output("shape-capsule-btn", "class_name"),
        Output("shape-oval-btn", "class_name"),
        Output("input-w", "value", allow_duplicate=True),
        Output("input-l", "value", allow_duplicate=True),
        Output("input-re", "value", allow_duplicate=True),
        Output("input-rs", "value", allow_duplicate=True),
        Output("input-dc", "value", allow_duplicate=True),
        Output("input-rc-min", "value", allow_duplicate=True),
        Output("input-rc-maj", "value", allow_duplicate=True),
        Output("input-land", "value", allow_duplicate=True),
        Output("input-hb", "value", allow_duplicate=True),
        Output("input-tt", "value", allow_duplicate=True),
        Output("input-density", "value", allow_duplicate=True),
        Output("input-weight", "value", allow_duplicate=True),
        Output("is-loading-preset", "data", allow_duplicate=True),
    ],
    [
        Input("shape-round-btn", "n_clicks"),
        Input("shape-capsule-btn", "n_clicks"),
        Input("shape-oval-btn", "n_clicks"),
    ],
    prevent_initial_call=True
)
def update_shape_selection(round_clicks, capsule_clicks, oval_clicks):
    trig = ctx.triggered_id
    new_shape = "round" # Default

    if trig == "shape-round-btn":
        new_shape = "round"
    elif trig == "shape-capsule-btn":
        new_shape = "capsule"
    elif trig == "shape-oval-btn":
        new_shape = "oval"
    else:
        return [dash.no_update] * 18

    def get_class(shape):
        base = "plotly-toolbar-btn"
        if new_shape == shape:
            return f"{base} active"
        return base
        
    # Дефолтные значения для сброса
    w = BASE_DEFAULTS["W"]
    l = BASE_DEFAULTS["L"]
    re = SHAPE_SPECIFIC[new_shape]["re"]
    rs = SHAPE_SPECIFIC[new_shape]["rs"]
    dc = BASE_DEFAULTS["dc"]
    rc_min = PROFILE_DEFAULTS["concave"]["rc_min"]
    rc_maj = PROFILE_DEFAULTS["concave"]["rc_maj"]
    land = BASE_DEFAULTS["land"]
    hb = BASE_DEFAULTS["hb"]
    tt = BASE_DEFAULTS["tt"]
    density = BASE_DEFAULTS["density"]
    weight = None # Пересчитается автоматически
    
    # Мы ставим is_loading=True, чтобы не сработали другие колбэки во время сброса, 
    # а потом система сама его скинет.
    return (
        new_shape, 
        "concave",
        get_class("round"), 
        get_class("capsule"), 
        get_class("oval"),
        w, l, re, rs, dc, rc_min, rc_maj, land, hb, tt, density, weight,
        True
    )
from core.engine import compute_bisect_width, compute_bisect_depth
from core.engine import generate_mesh


def _profile_options(shape, is_modified):
    if shape == "round":
        return [
            {"label": "Concave", "value": "concave"},
            {"label": "Compound Cup", "value": "compound"},
            {"label": "Concave Bevel Edge", "value": "cbe"},
            {"label": "Flat Face Radius Edge", "value": "ffre"},
            {"label": "Flat Face Bevel Edge", "value": "ffbe"},
        ]

    if shape == "capsule":
        if is_modified:
            return [
                {"label": "Concave", "value": "concave"},
                {"label": "Concave Bevel Edge", "value": "cbe"},
            ]
        return [
            {"label": "Concave", "value": "concave"},
            {"label": "Concave Bevel Edge", "value": "cbe"},
            {"label": "Flat Face Radius Edge", "value": "ffre"},
            {"label": "Flat Face Bevel Edge", "value": "ffbe"},
        ]

    return [
        {"label": "Concave", "value": "concave"},
        {"label": "Modified Oval", "value": "modified_oval"},
        {"label": "Compound Cup", "value": "compound"},
        {"label": "Concave Bevel Edge", "value": "cbe"},
        {"label": "Flat Face Radius Edge", "value": "ffre"},
        {"label": "Flat Face Bevel Edge", "value": "ffbe"},
    ]


def _bisect_options(profile):
    if profile in ("ffre", "ffbe"):
        return [
            {"label": "None", "value": "none"},
            {"label": "Cut Through", "value": "cut_through"},
        ]
    return [
        {"label": "None", "value": "none"},
        {"label": "Standard", "value": "standard"},
        {"label": "Cut Through", "value": "cut_through"},
        {"label": "Decreasing", "value": "decreasing"},
    ]


@callback(
    [Output("profile-dropdown", "options"), Output("profile-dropdown", "value")],
    [Input("shape-dropdown", "value"), Input("modified-switch", "value")],
    [State("profile-dropdown", "value"), State("is-loading-preset", "data")],
)
def update_profile_options(shape, is_modified, current_profile, is_loading):
    options = _profile_options(shape, bool(is_modified))
    available = {o["value"] for o in options}
    value = current_profile if current_profile in available else options[0]["value"]
    if is_loading:
        return options, dash.no_update
    return options, value


@callback(
    Output("profile-dropdown", "value", allow_duplicate=True),
    [
        Input("profile-btn-con", "n_clicks"),
        Input("profile-btn-com", "n_clicks"),
        Input("profile-btn-cbe", "n_clicks"),
        Input("profile-btn-ffre", "n_clicks"),
        Input("profile-btn-ffbe", "n_clicks"),
        Input("profile-btn-mod", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def set_profile_from_buttons(*_):
    trigger = ctx.triggered_id
    mapping = {
        "profile-btn-con": "concave",
        "profile-btn-com": "compound",
        "profile-btn-cbe": "cbe",
        "profile-btn-ffre": "ffre",
        "profile-btn-ffbe": "ffbe",
        "profile-btn-mod": "modified_oval",
    }
    return mapping.get(trigger, dash.no_update)


@callback(
    [
        Output("profile-btn-con", "style"),
        Output("profile-btn-com", "style"),
        Output("profile-btn-cbe", "style"),
        Output("profile-btn-ffre", "style"),
        Output("profile-btn-ffbe", "style"),
        Output("profile-btn-mod", "style"),
        Output("profile-btn-con", "active"),
        Output("profile-btn-com", "active"),
        Output("profile-btn-cbe", "active"),
        Output("profile-btn-ffre", "active"),
        Output("profile-btn-ffbe", "active"),
        Output("profile-btn-mod", "active"),
    ],
    [Input("shape-dropdown", "value"), Input("modified-switch", "value"), Input("profile-dropdown", "value")],
)
def sync_profile_buttons(shape, is_modified, profile):
    options = _profile_options(shape, bool(is_modified))
    ordered = [o["value"] for o in options]
    allowed = set(ordered)
    order_map = {value: idx for idx, value in enumerate(ordered, start=1)}
    first_visible = ordered[0] if ordered else None
    last_visible = ordered[-1] if ordered else None

    def style_for(value):
        if value not in allowed:
            return {"display": "none"}
        style = {"order": order_map.get(value, 99)}
        if value == first_visible:
            style.update({"borderTopLeftRadius": "6px", "borderBottomLeftRadius": "6px"})
        else:
            style.update({"borderTopLeftRadius": "0", "borderBottomLeftRadius": "0"})
        if value == last_visible:
            style.update({"borderTopRightRadius": "6px", "borderBottomRightRadius": "6px"})
        else:
            style.update({"borderTopRightRadius": "0", "borderBottomRightRadius": "0"})
        return style

    active_map = {
        "concave": False,
        "compound": False,
        "cbe": False,
        "ffre": False,
        "ffbe": False,
        "modified_oval": False,
    }
    if profile in active_map:
        active_map[profile] = True

    return (
        style_for("concave"),
        style_for("compound"),
        style_for("cbe"),
        style_for("ffre"),
        style_for("ffbe"),
        style_for("modified_oval"),
        active_map["concave"],
        active_map["compound"],
        active_map["cbe"],
        active_map["ffre"],
        active_map["ffbe"],
        active_map["modified_oval"],
    )


@callback(
    [Output("bisect-type", "options"), Output("bisect-type", "value")],
    [Input("profile-dropdown", "value")],
    [State("bisect-type", "value"), State("is-loading-preset", "data")],
)
def update_bisect_options(profile, current_type, is_loading):
    options = _bisect_options(profile)
    available = {o["value"] for o in options}
    value = current_type if current_type in available else options[0]["value"]
    if is_loading:
        return options, dash.no_update
    return options, value


@callback(
    Output("bisect-type", "value", allow_duplicate=True),
    [
        Input("bisect-btn-none", "n_clicks"),
        Input("bisect-btn-standard", "n_clicks"),
        Input("bisect-btn-cut", "n_clicks"),
        Input("bisect-btn-dec", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def set_bisect_type_from_buttons(*_):
    trig = ctx.triggered_id
    mapping = {
        "bisect-btn-none": "none",
        "bisect-btn-standard": "standard",
        "bisect-btn-cut": "cut_through",
        "bisect-btn-dec": "decreasing",
    }
    return mapping.get(trig, dash.no_update)


@callback(
    [
        Output("bisect-btn-none", "style"),
        Output("bisect-btn-standard", "style"),
        Output("bisect-btn-cut", "style"),
        Output("bisect-btn-dec", "style"),
        Output("bisect-btn-none", "active"),
        Output("bisect-btn-standard", "active"),
        Output("bisect-btn-cut", "active"),
        Output("bisect-btn-dec", "active"),
    ],
    [Input("profile-dropdown", "value"), Input("bisect-type", "value")],
)
def sync_bisect_buttons(profile, bisect_type):
    options = _bisect_options(profile)
    ordered = [o["value"] for o in options]
    allowed = set(ordered)
    first_visible = ordered[0] if ordered else None
    last_visible = ordered[-1] if ordered else None

    results = []
    # Styles
    for val in ["none", "standard", "cut_through", "decreasing"]:
        if val not in allowed:
            results.append({"display": "none"})
        else:
            style = {}
            if val == first_visible:
                style.update({"borderTopLeftRadius": "6px", "borderBottomLeftRadius": "6px"})
            else:
                style.update({"borderTopLeftRadius": "0", "borderBottomLeftRadius": "0"})
            if val == last_visible:
                style.update({"borderTopRightRadius": "6px", "borderBottomRightRadius": "6px"})
            else:
                style.update({"borderTopRightRadius": "0", "borderBottomRightRadius": "0"})
            results.append(style)

    # Active states
    for val in ["none", "standard", "cut_through", "decreasing"]:
        results.append(bisect_type == val)

    return results


@callback(
    [Output("div-bisect-double-sided", "style"), Output("bisect-double-sided", "value")],
    [Input("shape-dropdown", "value"), Input("bisect-type", "value")],
    [State("bisect-double-sided", "value"), State("is-loading-preset", "data")],
)
def toggle_double_sided_bisect(shape, b_type, current_value, is_loading):
    show = shape in ("capsule", "oval") and (b_type or "none") != "none"
    style = {"display": "block"} if show else {"display": "none"}
    if is_loading:
        return style, dash.no_update
    val = (current_value or []) if show else []
    return style, val


@callback(
    [Output("div-bisect-cruciform", "style"), Output("bisect-cruciform", "value")],
    [Input("shape-dropdown", "value"), Input("bisect-type", "value")],
    [State("bisect-cruciform", "value"), State("is-loading-preset", "data")],
)
def toggle_cruciform_bisect(shape, b_type, current_value, is_loading):
    show = shape == "round" and (b_type or "none") != "none"
    style = {"display": "block"} if show else {"display": "none"}
    if is_loading:
        return style, dash.no_update
    val = (current_value or []) if show else []
    return style, val


@callback(
    Output("bisect-edit-open", "data"),
    [Input("bisect-edit-btn", "n_clicks"), Input("bisect-type", "value")],
    [State("bisect-edit-open", "data")],
    prevent_initial_call=True,
)
def toggle_bisect_edit(n_clicks, b_type, is_open):
    b_type = b_type or "none"
    if b_type == "none":
        return False

    trigger = ctx.triggered_id
    if trigger == "bisect-edit-btn":
        return not bool(is_open)
    return bool(is_open)


@callback(
    [
        Output("div-bisect-controls-row", "style"),
        Output("bisect-edit-btn", "style"),
        Output("div-input-b-width", "style"),
        Output("div-input-b-depth", "style"),
        Output("div-input-b-angle", "style"),
        Output("div-input-b-ri", "style"),
    ],
    [Input("bisect-type", "value"), Input("bisect-edit-open", "data")],
)
def toggle_bisect_edit_fields(b_type, is_open):
    b_type = b_type or "none"
    show_row = {
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "width": "100%",
    }
    show_btn = {"display": "inline-flex"}
    hide = {"display": "none"}
    show_input = {"display": "block"}

    if b_type == "none":
        return hide, hide, hide, hide, hide, hide

    if bool(is_open):
        return show_row, show_btn, show_input, show_input, show_input, show_input
    return show_row, show_btn, hide, hide, hide, hide


@callback(
    [
        Output("label-input-w", "children"),
        Output("label-input-rc-min", "children"),
        Output("label-input-rc-maj", "children"),
        Output("div-input-l", "style"),
        Output("div-input-re", "style"),
        Output("div-input-rs", "style"),
        Output("div-input-rc-min", "style"),
        Output("div-input-rc-maj", "style"),
        Output("div-input-bev-d", "style"),
        Output("div-input-bev-a", "style"),
        Output("div-input-r-edge", "style"),
        Output("div-input-blend-r", "style"),
        Output("div-modified-switch", "style"),
        Output("div-input-r-maj-maj", "style"),
        Output("div-input-r-maj-min", "style"),
        Output("div-input-r-min-maj", "style"),
        Output("div-input-r-min-min", "style"),
        Output("input-rc-min", "disabled"),
        Output("input-rc-maj", "disabled"),
        Output("sidebar-container", "style"),
    ],
    [Input("shape-dropdown", "value"), Input("profile-dropdown", "value"), Input("lang-store", "data")],
)
def update_ui_visibility(shape, profile, lang):
    from core.i18n import t
    show = {"display": "block"}
    hide = {"display": "none"}
    reveal_style = {"opacity": "1", "transition": "opacity 0.1s"}

    label_w = t("dim.w", lang)
    label_rc_min = t("dim.rc_min", lang)
    label_rc_maj = t("dim.rc_maj", lang)
    vis_l = show
    vis_re = hide
    vis_rs = hide
    vis_rc_min = show
    vis_rc_maj = hide
    vis_bev_d = hide
    vis_bev_a = hide
    vis_r_edge = hide
    vis_blend_r = hide
    vis_mod_switch = hide
    vis_r_maj_maj = hide
    vis_r_maj_min = hide
    vis_r_min_maj = hide
    vis_r_min_min = hide
    rc_min_disabled = False
    rc_maj_disabled = True

    if shape == "round":
        label_w = t("dim.w_round", lang)
        vis_l = hide
    elif shape == "capsule":
        vis_mod_switch = show
        vis_re = show
        vis_rs = show
    else:
        vis_mod_switch = hide
        vis_re = show
        vis_rs = show
        vis_rc_maj = show
        rc_maj_disabled = False

    if profile in ("compound", "modified_oval"):
        vis_rc_min = show
        vis_rc_maj = hide
        vis_r_maj_maj = show
        vis_r_maj_min = show
        if shape == "oval" and profile == "compound":
            vis_r_min_maj = show
            vis_r_min_min = show
    elif profile == "cbe":
        vis_bev_d = show
        vis_bev_a = show
    elif profile == "ffre":
        vis_r_edge = show
    elif profile == "ffbe":
        vis_bev_a = show
        vis_blend_r = show

    if profile == "modified_oval":
        rc_min_disabled = True
    if shape == "oval" and profile == "concave":
        rc_min_disabled = True
        rc_maj_disabled = True
    if shape == "oval" and profile == "cbe":
        # minor and major cup radius locked, controlled by cup depth.
        rc_min_disabled = True
        rc_maj_disabled = True
    if shape == "oval" and profile in ("ffre", "ffbe"):
        rc_min_disabled = True
        rc_maj_disabled = True
    if shape == "oval" and profile == "compound":
        rc_min_disabled = True
        rc_maj_disabled = True
    if (shape == "round" and profile in ("ffre", "ffbe")) or (shape == "capsule" and profile in ("ffre", "ffbe")):
        rc_min_disabled = True

    if shape == "round" and profile in ("concave", "cbe"):
        rc_min_disabled = False
    if shape == "round" and profile == "compound":
        rc_min_disabled = True
    if shape == "capsule" and profile in ("concave", "cbe"):
        rc_min_disabled = False
    if shape == "capsule" and profile in ("ffre", "ffbe"):
        rc_min_disabled = True

    return (
        label_w,
        label_rc_min,
        label_rc_maj,
        vis_l,
        vis_re,
        vis_rs,
        vis_rc_min,
        vis_rc_maj,
        vis_bev_d,
        vis_bev_a,
        vis_r_edge,
        vis_blend_r,
        vis_mod_switch,
        vis_r_maj_maj,
        vis_r_maj_min,
        vis_r_min_maj,
        vis_r_min_min,
        rc_min_disabled,
        rc_maj_disabled,
        reveal_style
    )


@callback(
    [Output("input-re", "disabled"), Output("input-rs", "disabled")],
    [Input("shape-dropdown", "value"), Input("modified-switch", "value")],
)
def lock_radii_inputs(shape, is_modified):
    if shape == "capsule" and not bool(is_modified):
        return True, True
    return False, False


@callback(
    [Output("input-w", "value", allow_duplicate=True), Output("input-l", "value")],
    [Input("input-w", "value"), Input("input-l", "value")],
    [State("is-loading-preset", "data")],
    prevent_initial_call=True,
)
def clamp_main_axes_non_negative(w, l, is_loading):
    if is_loading:
        return dash.no_update, dash.no_update
        
    trigger = ctx.triggered_id
    out_w = dash.no_update
    out_l = dash.no_update

    if trigger == "input-w" and w is not None:
        if w < 0.01:
            out_w = 0.01
            w = 0.01
        elif w > 25.0:
            out_w = 25.0
            w = 25.0
        if l is not None and w > l:
            out_l = w

    if trigger == "input-l" and l is not None:
        if l < 0.01:
            out_l = 0.01
            l = 0.01
        elif l > 25.0:
            out_l = 25.0
            l = 25.0
        if w is not None and l < w:
            out_l = w
    return out_w, out_l


@callback(
    [Output("input-re", "value"), Output("input-rs", "value")],
    [
        Input("shape-dropdown", "value"),
        Input("modified-switch", "value"),
        Input("profile-dropdown", "value"),
        Input("input-w", "value"),
        Input("input-l", "value"),
        Input("input-land", "value"),
        Input("input-dc", "value"),
        Input("input-r-edge", "value"),
        Input("input-blend-r", "value"),
        Input("input-bev-a", "value"),
        Input("input-re", "value"),
        Input("input-rs", "value"),
    ],
    [State("is-loading-preset", "data")],
    prevent_initial_call=True,
)
def sync_end_side_radii(shape, is_modified, profile, w, l, land, dc, r_edge, blend_r, bev_a, re, rs, is_loading):
    if is_loading:
        return dash.no_update, dash.no_update
        
    if w is None or l is None:
        return dash.no_update, dash.no_update

    is_mod = bool(is_modified)
    if shape not in ("oval", "capsule"):
        return dash.no_update, dash.no_update
    if shape == "capsule" and not is_mod:
        return round(max(0.01, w / 2), 2), 0.0

    w = max(0.1, w)
    l = max(w, l)
    land_val = 0.01 if land is None else max(0.01, land)
    dc_val = 0.01 if dc is None else max(0.01, dc)
    trigger = ctx.triggered_id
    is_capsule_mod_concave = shape == "capsule" and is_mod and profile in ("concave", "cbe")
    is_oval_flat = shape == "oval" and profile in ("ffre", "ffbe")

    # Bounds for End Radius / Side Radius.
    re_min = 0.1 if is_capsule_mod_concave else 0.01
    if is_oval_flat:
        inset = 0.0
        if profile == "ffre":
            r_edge_val = 0.01 if r_edge is None else max(0.01, r_edge)
            disc = r_edge_val**2 - (r_edge_val - dc_val) ** 2
            inset = np.sqrt(max(0.0, disc))
        else:  # ffbe
            rb = 0.01 if blend_r is None else max(0.01, min(blend_r, dc_val))
            bev_a_val = 40.0 if bev_a is None else min(60.0, bev_a)
            alpha = np.radians(bev_a_val)
            if 1e-6 < alpha < (np.pi / 2 - 1e-6):
                tan_a = np.tan(alpha)
                sin_a = np.sin(alpha)
                if abs(tan_a) > 1e-9 and abs(sin_a) > 1e-9:
                    inset = (dc_val - rb) / tan_a + rb / sin_a
        # Re_flat = Re - Land - inset must stay > 0 for non-degenerate flat platform.
        re_min = max(re_min, land_val + inset + 0.01)
    re_max = max(re_min, w / 2 - 0.01)

    def _rs_from_re(re_val):
        den = w - 2 * re_val
        if den <= 1e-8:
            return float("inf")
        num = (l / 2 - re_val) ** 2 + (w / 2) ** 2 - re_val**2
        return num / den

    rs_min = max(l / 2 + 0.01, _rs_from_re(re_min))
    rs_max = max(rs_min, _rs_from_re(re_max))

    re_val = re_max if re is None else re
    re_val = min(max(re_min, re_val), re_max)

    apply_rs_re_bounds = is_capsule_mod_concave or is_oval_flat

    if trigger == "input-rs":
        if rs is None:
            return dash.no_update, dash.no_update
        rs_val = rs
        rs_out = dash.no_update
        if apply_rs_re_bounds:
            rs_val_clamped = min(max(rs_min, rs_val), rs_max)
            if abs(rs_val_clamped - rs_val) > 1e-9:
                rs_out = round(rs_val_clamped, 4)
            rs_val = rs_val_clamped
        elif rs_val <= l / 2 + 1e-6:
            return dash.no_update, dash.no_update
        denom = 2 * rs_val - l
        new_re = (rs_val * w - (w / 2) ** 2 - (l / 2) ** 2) / denom if denom > 1e-8 else -1
        if new_re <= 0:
            new_re = re_min
        new_re = min(max(re_min, new_re), re_max)
        # Do not overwrite the field currently being typed by the user.
        return round(new_re, 4), rs_out

    rs_calc = _rs_from_re(re_val)
    rs_calc = max(l / 2 + 0.01, rs_calc)
    if apply_rs_re_bounds:
        rs_calc = min(max(rs_min, rs_calc), rs_max)
        re_out = dash.no_update
        if re is None or abs(re_val - re) > 1e-9:
            re_out = round(re_val, 4)
        return re_out, round(rs_calc, 4)
    # Keep typed End Radius untouched; update only dependent Side Radius.
    return dash.no_update, round(rs_calc, 4)


@callback(
    [
        Output("input-b-width", "value"),
        Output("input-b-depth", "value"),
        Output("input-b-angle", "value"),
        Output("input-b-ri", "value"),
    ],
    [
        Input("bisect-type", "value"),
        Input("input-b-width", "value"),
        Input("input-b-depth", "value"),
        Input("input-dc", "value"),
        Input("input-b-angle", "value"),
        Input("input-b-ri", "value"),
    ],
    [
        State("shape-dropdown", "value"),
        State("profile-dropdown", "value"),
        State("modified-switch", "value"),
        State("input-w", "value"),
        State("input-l", "value"),
        State("input-re", "value"),
        State("input-rs", "value"),
        State("input-land", "value"),
        State("input-rc-min", "value"),
        State("input-r-maj-maj", "value"),
        State("input-r-maj-min", "value"),
        State("input-bev-d", "value"),
        State("input-bev-a", "value"),
        State("input-r-edge", "value"),
        State("input-blend-r", "value"),
        State("is-loading-preset", "data"),
    ],
)
def sync_bisect_logic(
    b_type,
    b_width,
    b_depth,
    dc,
    b_angle,
    b_ri,
    shape,
    profile,
    is_modified,
    w,
    l,
    re,
    rs,
    land,
    rc_min,
    r_maj_maj,
    r_maj_min,
    bev_d,
    bev_a,
    r_edge,
    blend_r,
    is_loading,
):
    if is_loading:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
    trigger = ctx.triggered_id
    if dc is None or w is None or profile is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    params = {
        "shape": shape,
        "profile": profile,
        "is_modified": bool(is_modified),
        "W": w,
        "L": l if l is not None else BASE_DEFAULTS["L"],
        "Re": re if re is not None else SHAPE_SPECIFIC["oval"]["re"],
        "Rs": rs if rs is not None else SHAPE_SPECIFIC["oval"]["rs"],
        "Land": land or 0.0,
        "Dc": dc,
        "Rc_min": rc_min or 8.8,
        "R_maj_maj": r_maj_maj or 88.9,
        "R_maj_min": r_maj_min or 6.35,
        "Bev_D": bev_d if bev_d is not None else 0.51,
        "Bev_A": 40.0 if bev_a is None else min(60.0, bev_a),
        "R_edge": r_edge if r_edge is not None else 6.35,
        "Blend_R": blend_r if blend_r is not None else 0.38,
    }

    max_d = round(dc * 0.95, 4)
    safe_angle = b_angle if b_angle is not None else 90.0
    safe_ri = b_ri if b_ri is not None else 0.06

    if trigger is None or trigger == "bisect-type":
        if b_type == "none":
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        angle, ri = 90.0, 0.06
        depth = round(dc * 0.95, 4) if b_type == "cut_through" else round(dc * 0.34 - 0.005, 4)
        width = compute_bisect_width(params, depth, angle, ri)
        return round(width, 4), depth, angle, ri

    if trigger == "input-b-width":
        if b_width is None:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        depth = compute_bisect_depth(params, b_width, safe_angle, safe_ri)

        if depth > max_d:
            depth = max_d
            width = compute_bisect_width(params, depth, safe_angle, safe_ri)
            return round(width, 4), depth, dash.no_update, dash.no_update

        return dash.no_update, depth, dash.no_update, dash.no_update

    if b_depth is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    safe_depth = min(b_depth, max_d)
    width = compute_bisect_width(params, safe_depth, safe_angle, safe_ri)

    if b_depth > max_d:
        return round(width, 4), safe_depth, dash.no_update, dash.no_update
    return round(width, 4), dash.no_update, dash.no_update, dash.no_update


@callback(
    [
        Output("input-hb", "value"),
        Output("input-tt", "value"),
    ],
    [
        Input("input-hb", "value"),
        Input("input-tt", "value"),
        Input("input-dc", "value"),
        Input("input-w", "value"),
        Input("input-land", "value"),
    ],
    [
        State("is-loading-preset", "data"), 
        State("shape-dropdown", "value"),
        State("profile-dropdown", "value"),
        State("input-bev-d", "value"),
        State("input-bev-a", "value"),
        State("input-r-edge", "value"),
        State("input-blend-r", "value"),
        State("input-r-maj-maj", "value"),
        State("input-r-maj-min", "value"),
    ],
    prevent_initial_call=True,
)
def sync_physical_params(hb, tt, dc, w, land, is_loading, shape, profile, bev_d, bev_a, r_edge, blend_r, r_mm, r_mn):
    if is_loading:
        return dash.no_update, dash.no_update
        
    trigger = ctx.triggered_id
    if any(v is None for v in [hb, tt, dc, w]):
        return dash.no_update, dash.no_update
    # RULE: Diameter/width (W) limits Tt and Dc
    if shape == "round":
        land_val = land if land is not None else 0.08
        concave_span = max(0.01, w / 2 - land_val - 0.01)
        max_dc = round(concave_span, 4)

        # 1. Cup Depth (Dc) profile max
        if profile == "ffre":
            r_edge_val = r_edge if r_edge is not None else PROFILE_DEFAULTS["ffre"]["r_edge"]
            ffre_max = _ffre_dc_max_from_r_edge(concave_span, r_edge_val)
            if ffre_max is not None: max_dc = min(max_dc, round(ffre_max, 4))
        elif profile == "ffbe":
            blend_r_val = blend_r if blend_r is not None else PROFILE_DEFAULTS["ffbe"]["blend_r"]
            bev_a_val = bev_a if bev_a is not None else PROFILE_DEFAULTS["cbe"]["bev_a"]
            ffbe_max = _ffbe_dc_max_from_ref_flat(concave_span, blend_r_val, bev_a_val)
            if ffbe_max is not None: max_dc = min(max_dc, round(ffbe_max, 4))
        elif profile == "cbe":
            b_d = bev_d if bev_d is not None else 0.51
            bev_a_val = bev_a if bev_a is not None else PROFILE_DEFAULTS["cbe"]["bev_a"]
            cbe_max, _ = _round_cbe_tangent_limits(concave_span, b_d, bev_a_val)
            if cbe_max is not None: max_dc = min(max_dc, round(cbe_max, 4))
        elif profile == "compound":
            r_mm_val = r_mm if r_mm is not None else PROFILE_DEFAULTS["compound"]["r_maj_maj"]
            r_mn_val = r_mn if r_mn is not None else PROFILE_DEFAULTS["compound"]["r_maj_min"]
            _, c_max = _compound_dc_bounds(concave_span, r_mm_val, r_mn_val)
            if c_max is not None: max_dc = min(max_dc, round(c_max, 4))

        current_dc = min(dc, max_dc)
    else:
        current_dc = dc

    # 2. Tablet Thickness (Tt) limit for ALL shapes
    if tt > w:
        tt = w
        hb = round(tt - 2 * current_dc, 4)

    # 3. Trigger handling
    if trigger == "input-tt":
        if tt > w: tt = w
        new_hb = round(tt - 2 * current_dc, 4)
        if new_hb < 0.01:
            return 0.01, round(2 * current_dc + 0.01, 4)
        return new_hb, tt

    if trigger in ("input-hb", "input-dc", "input-w"):
        if hb + 2 * current_dc > w:
            tt = w
            hb = round(tt - 2 * current_dc, 4)

        hb_final = max(0.01, hb)
        return hb_final, round(hb_final + 2 * current_dc, 4)

    return dash.no_update, dash.no_update


def _build_mass_params(
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
    }


@callback(
    [
        Output("input-tt", "value", allow_duplicate=True),
        Output("input-weight", "value"),
    ],
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
        Input("input-weight", "value"),
    ],
    [State("is-loading-preset", "data")],
    prevent_initial_call="initial_duplicate",
)
def sync_weight_density_with_volume(
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
    weight,
    is_loading,
):
    if is_loading:
        return dash.no_update, dash.no_update
        
    # ПРАВИЛО: Если значения стерты, используем дефолты для расчетов
    w_val = BASE_DEFAULTS["W"] if w is None else max(0.1, w)
    dc_val = BASE_DEFAULTS["dc"] if dc is None else max(0.0, dc)

    try:
        density_val = BASE_DEFAULTS["density"] if density is None else max(0.01, float(density))
        tt_val = BASE_DEFAULTS["tt"] if tt is None else float(tt)
        dc_val_safe = float(dc_val)
        hb_val = max(0.01, tt_val - 2.0 * dc_val_safe)

        params = _build_mass_params(
            shape,
            profile,
            is_mod,
            w_val,
            l or BASE_DEFAULTS["L"],
            re or SHAPE_SPECIFIC["oval"]["re"],
            rs or SHAPE_SPECIFIC["oval"]["rs"],
            dc_val_safe,
            rc_min or PROFILE_DEFAULTS["concave"]["rc_min"],
            rc_maj or PROFILE_DEFAULTS["concave"]["rc_maj"],
            land or BASE_DEFAULTS["land"],
            hb_val,
            bev_d or PROFILE_DEFAULTS["cbe"]["bev_d"],
            bev_a if bev_a is not None else PROFILE_DEFAULTS["cbe"]["bev_a"],
            r_edge or PROFILE_DEFAULTS["ffre"]["r_edge"],
            blend_r if blend_r is not None else PROFILE_DEFAULTS["ffbe"]["blend_r"],
            r_maj_maj or PROFILE_DEFAULTS["compound"]["r_maj_maj"],
            r_maj_min or PROFILE_DEFAULTS["compound"]["r_maj_min"],
            r_min_maj or PROFILE_DEFAULTS["compound"]["r_min_maj"],
            r_min_min or PROFILE_DEFAULTS["compound"]["r_min_min"],
            b_type,
            b_width,
            b_depth,
            b_angle,
            b_ri,
            b_cruciform,
            b_double_sided,
        )
        mesh = generate_mesh(params)
        m = mesh["metrics"]
        # mm3 * g/cm3 == mg (numerically)
        vol_now = float(m.get("Tablet_Vol", 0.0))
        die_hole_sa = float(m.get("Die_Hole_SA", 0.0))
        # Constant volume part that does not depend on belly band (both cups + lands + groove effects).
        fixed_vol = max(0.0, vol_now - die_hole_sa * hb_val)
        expected_weight = density_val * vol_now

        trig = ctx.triggered_id
        if trig == "input-weight" and weight is not None and die_hole_sa > 1e-9:
            target_weight = max(0.0, float(weight))
            # Ignore self-trigger when weight was just auto-updated from geometry/density.
            if abs(target_weight - expected_weight) <= max(1e-4, expected_weight * 1e-4):
                return dash.no_update, round(expected_weight, 4)

            target_vol = target_weight / density_val
            hb_new = max(0.01, (target_vol - fixed_vol) / die_hole_sa)
            tt_new = hb_new + 2.0 * dc_val
            actual_vol = die_hole_sa * hb_new + fixed_vol
            actual_weight = density_val * actual_vol
            return round(tt_new, 4), round(actual_weight, 4)

        return dash.no_update, round(expected_weight, 4)
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        print(f"Error in sync_weight_density_with_volume: {e}")
        return dash.no_update, dash.no_update


@callback(
    Output("tip-force-value", "value"),
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
        Input("bisect-cruciform", "value"),
        Input("bisect-double-sided", "value"),
        Input("input-tip-force-steel", "value"),
    ],
)
def update_tip_force_value(
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
    b_cruciform,
    b_double_sided,
    steel,
):
    params = {
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
        "Bev_D": bev_d if bev_d is not None else PROFILE_DEFAULTS["cbe"]["bev_d"],
        "Bev_A": bev_a if bev_a is not None else PROFILE_DEFAULTS["cbe"]["bev_a"],
        "R_edge": r_edge if r_edge is not None else PROFILE_DEFAULTS["ffre"]["r_edge"],
        "Blend_R": blend_r if blend_r is not None else PROFILE_DEFAULTS["ffbe"]["blend_r"],
        "R_maj_maj": r_maj_maj if r_maj_maj is not None else PROFILE_DEFAULTS["compound"]["r_maj_maj"],
        "R_maj_min": r_maj_min if r_maj_min is not None else PROFILE_DEFAULTS["compound"]["r_maj_min"],
        "R_min_maj": r_min_maj if r_min_maj is not None else PROFILE_DEFAULTS["compound"]["r_min_maj"],
        "R_min_min": r_min_min if r_min_min is not None else PROFILE_DEFAULTS["compound"]["r_min_min"],
        "b_type": b_type if b_type is not None else "none",
        "b_cruciform": bool(b_cruciform and "on" in b_cruciform),
        "b_double_sided": bool(b_double_sided and "on" in b_double_sided),
        "tip_force_steel": steel if steel else BASE_DEFAULTS["tip_force_steel"],
    }

    tip_force = calculate_tip_force(params)
    if not tip_force["supported"] or tip_force["selected_force"] is None:
        return "N/A"
    return f'{tip_force["selected_force"]}'


def _calc_rc_from_dc(span, dc):
    if span <= 0 or dc is None or dc <= 0:
        return None
    return (span**2 + dc**2) / (2 * dc)


def _calc_dc_from_rc(span, rc):
    if span <= 0 or rc is None or rc <= span:
        return None
    disc = rc**2 - span**2
    if disc < 0:
        return None
    return rc - np.sqrt(disc)


def _calc_cbe_rc_from_dc(span, dc, bev_d, bev_a):
    if span <= 0 or dc is None or dc <= 0:
        return None
    alpha = np.radians(bev_a)
    if alpha <= 1e-6 or alpha >= np.pi / 2 - 1e-6:
        return None
    db = 0.0 if bev_d is None else max(0.0, min(bev_d, dc - 1e-6))
    hc = dc - db
    if hc <= 1e-6:
        return None
    tan_a = np.tan(alpha)
    if abs(tan_a) <= 1e-9:
        return None
    r_in = span - db / tan_a
    if r_in <= 1e-6:
        return None
    return (r_in**2 + hc**2) / (2 * hc)


def _calc_dc_from_cbe_rc(span, rc, bev_d, bev_a):
    if span <= 0 or rc is None:
        return None
    alpha = np.radians(bev_a)
    if alpha <= 1e-6 or alpha >= np.pi / 2 - 1e-6:
        return None
    db = max(0.0, 0.0 if bev_d is None else bev_d)
    tan_a = np.tan(alpha)
    if abs(tan_a) <= 1e-9:
        return None
    r_in = span - db / tan_a
    if r_in <= 1e-6 or rc <= r_in:
        return None
    hc = _calc_dc_from_rc(r_in, rc)
    if hc is None:
        return None
    return hc + db


def _compound_dc_bounds(span, r_maj, r_min):
    if span <= 0 or r_maj is None or r_min is None:
        return None, None
    if r_maj < span or r_min < span:
        return None, None
    d_min = r_maj - np.sqrt(max(0.0, r_maj**2 - span**2))
    d_max = r_min - np.sqrt(max(0.0, r_min**2 - span**2))
    return d_min, d_max


def _round_cbe_tangent_limits(span, bev_d, bev_a_deg):
    if span <= 0 or bev_d is None or bev_a_deg is None:
        return None, None
    alpha = np.radians(bev_a_deg)
    if alpha <= 1e-6 or alpha >= np.pi / 2 - 1e-6:
        return None, None
    tan_a = np.tan(alpha)
    if abs(tan_a) <= 1e-9:
        return None, None
    db = max(0.0, bev_d)
    r_in = span - db / tan_a
    if r_in <= 1e-9:
        return None, None
    # Tangency-limited maximum cup depth:
    # hc_max = r_in * tan(alpha/2), Dc_max = Db + hc_max
    hc_max = r_in * np.tan(alpha / 2.0)
    dc_max = db + hc_max
    # Equivalent minimum cup radius at tangency limit:
    # Rc_min = r_in / sin(alpha)
    sin_a = np.sin(alpha)
    rc_min = r_in / sin_a if sin_a > 1e-9 else None
    return dc_max, rc_min


def _ffre_dc_max_from_r_edge(span, r_edge):
    if span <= 0 or r_edge is None or r_edge < span:
        return None
    return r_edge - np.sqrt(max(0.0, r_edge**2 - span**2))


def _ffbe_dc_max_from_ref_flat(span, blend_r, bev_a_deg, ref_flat_min=0.1):
    if span <= 0 or blend_r is None or bev_a_deg is None:
        return None
    alpha = np.radians(bev_a_deg)
    if alpha <= 1e-6 or alpha >= np.pi / 2 - 1e-6:
        return None
    tan_a = np.tan(alpha)
    sin_a = np.sin(alpha)
    if abs(tan_a) <= 1e-9 or abs(sin_a) <= 1e-9:
        return None

    rb = max(0.0, blend_r)
    # For round/capsule front view in FFBE:
    # r_flat = span - D_inset, RefFlat = 2*r_flat.
    # Keep RefFlat >= ref_flat_min  =>  D_inset <= span - ref_flat_min/2.
    d_inset_max = span - ref_flat_min / 2.0
    rhs = d_inset_max - rb / sin_a
    dc_max = rb + tan_a * rhs
    return dc_max


def _clamp_to_step_range(value, lo, hi, step=0.01):
    if value is None or lo is None or hi is None:
        return None
    lo_v, hi_v = (lo, hi) if lo <= hi else (hi, lo)
    v = min(max(value, lo_v), hi_v)
    # Keep number on UI step-grid to avoid browser "nearest valid values" error.
    k = np.floor((v + 1e-12) / step) if v >= hi_v else np.round(v / step)
    v_step = float(k * step)
    v_step = min(max(v_step, lo_v), hi_v)
    # If rounded point escaped above hi due step-grid, move one step down.
    if v_step > hi_v:
        v_step = max(lo_v, v_step - step)
    return round(v_step, 4)


@callback(
    [
        Output("input-rc-min", "value", allow_duplicate=True), 
        Output("input-rc-maj", "value", allow_duplicate=True), 
        Output("input-dc", "value", allow_duplicate=True),
        Output("input-w", "value", allow_duplicate=True),
        Output("input-r-maj-maj", "value", allow_duplicate=True),
        Output("input-r-maj-min", "value", allow_duplicate=True),
        Output("input-bev-a", "value", allow_duplicate=True),
    ],
    [
        Input("shape-dropdown", "value"),
        Input("profile-dropdown", "value"),
        Input("modified-switch", "value"),
        Input("input-w", "value"),
        Input("input-l", "value"),
        Input("input-land", "value"),
        Input("input-blend-r", "value"),
        Input("input-r-edge", "value"),
        Input("input-r-maj-maj", "value"),
        Input("input-r-maj-min", "value"),
        Input("input-bev-d", "value"),
        Input("input-bev-a", "value"),
        Input("input-dc", "value"),
        Input("input-rc-min", "value"),
        Input("input-rc-maj", "value"),
    ],
    [
        State("is-loading-preset", "data"),
        State("input-w", "value"),
        State("input-dc", "value"),
        State("input-rc-min", "value"),
        State("input-rc-maj", "value"),
        State("input-r-maj-maj", "value"),
        State("input-r-maj-min", "value"),
        State("input-bev-a", "value"),
    ],
    prevent_initial_call=True,
)
def sync_cup_radii_depth(shape, profile, is_modified, w, l, land, blend_r, r_edge, r_maj_maj, r_maj_min, bev_d, bev_a, dc, rc_min, rc_maj, is_loading, w_s, dc_s, rc_min_s, rc_maj_s, r_mm_s, r_mn_s, bev_a_s):
    if is_loading:
        return [dash.no_update] * 7
        
    trig = ctx.triggered_id

    # --- ГЛОБАЛЬНЫЕ ПРАВИЛА ВАЛИДАЦИИ ---
    # 1. Если поле стерто (None), восстанавливаем из State.
    w_f = w if w is not None else (w_s or BASE_DEFAULTS["W"])
    dc_f = dc if dc is not None else (dc_s or BASE_DEFAULTS["dc"])
    r_mm_f = r_maj_maj if r_maj_maj is not None else (r_mm_s or PROFILE_DEFAULTS["compound"]["r_maj_maj"])
    r_mn_f = r_maj_min if r_maj_min is not None else (r_mn_s or PROFILE_DEFAULTS["compound"]["r_maj_min"])
    bev_a_f = bev_a if bev_a is not None else (bev_a_s or PROFILE_DEFAULTS["cbe"]["bev_a"])

    # 2. Ограничение Bevel Angle (Max 60) - СКВОЗНОЕ ДЛЯ ВСЕХ ФОРМ
    if bev_a_f > 60.0:
        bev_a_f = 60.0
    # -----------------------------------

    w_val = max(0.1, w_f)
    l_val = max(w_val, w_val if l is None else l)
    land_val = 0.08 if land is None else max(0.0, land)
    s_min = max(0.001, w_val / 2 - land_val)
    s_maj = max(0.001, l_val / 2 - land_val)
    is_mod = bool(is_modified)

    editable_min = (
        (shape == "round" and profile in ("concave", "cbe"))
        or (shape == "capsule" and profile in ("concave", "cbe"))
    )
    editable_maj = False
    is_round_concave = shape == "round" and profile == "concave"
    is_capsule_concave = shape == "capsule" and profile == "concave"
    is_oval_concave = shape == "oval" and profile == "concave"

    # Ограничение Cup Depth
    min_dc = 0.01
    if profile == "cbe":
        min_dc = round((bev_d if bev_d is not None else 0.51) + 0.01, 4)
    if dc_f < min_dc: dc_f = min_dc

    # Round/Capsule/Oval Concave constraints
    concave_span = max(0.0, w_val / 2 - land_val)
    if is_round_concave or is_capsule_concave or is_oval_concave:
        if dc_f > concave_span:
            dc_f = _clamp_to_step_range(concave_span, 0.01, concave_span, step=0.01)
        
        if trig == "input-rc-min" and rc_min is not None:
            if rc_min < concave_span:
                rc_min = round(float(np.ceil(concave_span / 0.01) * 0.01), 4)
            new_dc = _calc_dc_from_rc(s_min, rc_min)
            if new_dc is not None: dc_f = new_dc

    # CBE tangent limits
    if shape in ("round", "capsule") and profile == "cbe":
        b_d = 0.51 if bev_d is None else bev_d
        dc_max_tan, rc_min_tan = _round_cbe_tangent_limits(concave_span, b_d, bev_a_f)
        if dc_max_tan is not None and dc_f > dc_max_tan:
            dc_f = _clamp_to_step_range(dc_max_tan, 0.01, dc_max_tan, step=0.01)
        
        if trig == "input-rc-min" and rc_min is not None and rc_min_tan is not None:
            if rc_min < rc_min_tan:
                rc_min = round(float(np.ceil(rc_min_tan / 0.01) * 0.01), 4)
            new_dc = _calc_dc_from_cbe_rc(s_min, rc_min, b_d, bev_a_f)
            if new_dc is not None: dc_f = new_dc

    # Compound Cup bounds (Round)
    if shape == "round" and profile == "compound":
        d_min, d_max = _compound_dc_bounds(concave_span, r_mm_f, r_mn_f)
        if d_min is not None and d_max is not None:
            lo, hi = (min(d_min, d_max), max(d_min, d_max))
            if dc_f < lo: dc_f = lo
            if dc_f > hi: dc_f = hi

    # Flat Face constraints (FFRE/FFBE)
    if profile == "ffre":
        r_edge_val = r_edge if r_edge is not None else PROFILE_DEFAULTS["ffre"]["r_edge"]
        dc_max_ffre = _ffre_dc_max_from_r_edge(concave_span, r_edge_val)
        if dc_max_ffre is not None and dc_f > dc_max_ffre:
            dc_f = _clamp_to_step_range(dc_max_ffre, 0.01, dc_max_ffre, step=0.01)
            
    if profile == "ffbe":
        blend_r_val = blend_r if blend_r is not None else PROFILE_DEFAULTS["ffbe"]["blend_r"]
        dc_max_ffbe = _ffbe_dc_max_from_ref_flat(concave_span, blend_r_val, bev_a_f)
        if dc_max_ffbe is not None and dc_f > dc_max_ffbe:
            dc_f = _clamp_to_step_range(dc_max_ffbe, 0.01, dc_max_ffbe, step=0.01)

    # Final calculations for Rc values
    def rc_min_from_dc(v):
        if profile == "cbe": return _calc_cbe_rc_from_dc(s_min, v, bev_d or 0.51, bev_a_f)
        return _calc_rc_from_dc(s_min, v)

    def rc_maj_from_dc(v):
        if shape == "oval":
            if profile == "cbe": return _calc_cbe_rc_from_dc(s_maj, v, bev_d or 0.51, bev_a_f)
            if profile == "concave": return _calc_rc_from_dc(s_maj, v)
        return None

    new_rc_min = rc_min_from_dc(dc_f)
    new_rc_maj = rc_maj_from_dc(dc_f)

    out_rc_min = round(new_rc_min, 4) if new_rc_min is not None else dash.no_update
    out_rc_maj = round(new_rc_maj, 4) if new_rc_maj is not None else dash.no_update
    out_dc = round(dc_f, 4) if round(dc_f, 4) != dc else dash.no_update
    out_w = round(w_f, 4) if round(w_f, 4) != w else dash.no_update
    out_rmm = round(r_mm_f, 4) if round(r_mm_f, 4) != r_maj_maj else dash.no_update
    out_rmn = round(r_mn_f, 4) if round(r_mn_f, 4) != r_maj_min else dash.no_update
    out_beva = round(bev_a_f, 4) if round(bev_a_f, 4) != bev_a else dash.no_update

    if trig == "input-rc-min" and editable_min:
        curr_rc = rc_min if rc_min is not None else rc_min_s
        if curr_rc: out_rc_min = curr_rc
    if trig == "input-rc-maj" and editable_maj:
        curr_rc = rc_maj if rc_maj is not None else rc_maj_s
        if curr_rc: out_rc_maj = curr_rc

    return (
        out_rc_min,
        out_rc_maj,
        out_dc,
        out_w,
        out_rmm,
        out_rmn,
        out_beva
    )
