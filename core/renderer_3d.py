import numpy as np
import plotly.graph_objects as go

from core.domain.shapes import shape_params


def _get_circle_contour(radius, density=220):
    t = np.linspace(0, 2 * np.pi, density)
    return radius * np.cos(t), radius * np.sin(t)


def _get_capsule_contour(l_val, w_val, density=150):
    r = w_val / 2
    l_flat = max(0, l_val - w_val)
    t_right = np.linspace(0, np.pi, density)
    x_right = l_flat / 2 + r * np.sin(t_right)
    y_right = r * np.cos(t_right)
    x_bottom = np.linspace(l_flat / 2, -l_flat / 2, density)
    y_bottom = np.full_like(x_bottom, -r)
    t_left = np.linspace(np.pi, 2 * np.pi, density)
    x_left = -l_flat / 2 + r * np.sin(t_left)
    y_left = r * np.cos(t_left)
    x_top = np.linspace(-l_flat / 2, l_flat / 2, density)
    y_top = np.full_like(x_top, r)
    x = np.concatenate([x_right, x_bottom, x_left, x_top])
    y = np.concatenate([y_right, y_bottom, y_left, y_top])
    return x, y


def _get_oval_contour(l_val, w_val, re, rs, density=120):
    xe = l_val / 2 - re
    ys = w_val / 2 - rs
    gamma = np.arctan2(abs(ys), max(1e-6, xe))
    t1 = np.linspace(-gamma, gamma, density)
    t2 = np.linspace(gamma, np.pi - gamma, density)
    t3 = np.linspace(np.pi - gamma, np.pi + gamma, density)
    t4 = np.linspace(np.pi + gamma, 2 * np.pi - gamma, density)
    c1_x, c1_y = xe + re * np.cos(t1), re * np.sin(t1)
    c2_x, c2_y = rs * np.cos(t2), ys + rs * np.sin(t2)
    c3_x, c3_y = -xe + re * np.cos(t3), re * np.sin(t3)
    c4_x, c4_y = rs * np.cos(t4), -ys + rs * np.sin(t4)
    x = np.concatenate([c1_x, c2_x, c3_x, c4_x, [c1_x[0]]])
    y = np.concatenate([c1_y, c2_y, c3_y, c4_y, [c1_y[0]]])
    return x, y


def _shape_contour(params):
    shape, is_modified, w_val, l_val, _, re, rs = shape_params(params)
    if shape == "round":
        return _get_circle_contour(w_val / 2)
    if shape == "capsule" and not is_modified:
        return _get_capsule_contour(l_val, w_val)
    return _get_oval_contour(l_val, w_val, re, rs)


def _shape_contour_inner(params):
    shape, is_modified, w_val, l_val, land, re, rs = shape_params(params)
    if land <= 1e-9:
        return _shape_contour(params)
    if shape == "round":
        return _get_circle_contour(max(0.01, w_val / 2 - land))
    if shape == "capsule" and not is_modified:
        return _get_capsule_contour(max(0.1, l_val - 2 * land), max(0.1, w_val - 2 * land))
    re_in = max(0.01, re - land)
    rs_in = max(0.01, rs - land)
    return _get_oval_contour(max(0.1, l_val - 2 * land), max(0.1, w_val - 2 * land), re_in, rs_in)


def _boundary_radius_from_contour(x_c, y_c, theta_query):
    theta_c = np.mod(np.arctan2(y_c, x_c), 2 * np.pi)
    r_c = np.hypot(x_c, y_c)
    order = np.argsort(theta_c)
    theta_s = theta_c[order]
    r_s = r_c[order]
    theta_u, idx = np.unique(theta_s, return_index=True)
    r_u = r_s[idx]
    theta_ext = np.concatenate(([theta_u[-1] - 2 * np.pi], theta_u, [theta_u[0] + 2 * np.pi]))
    r_ext = np.concatenate(([r_u[-1]], r_u, [r_u[0]]))
    return np.interp(theta_query, theta_ext, r_ext)


def _interp_bilinear(z_arr, x_grid, y_grid, xq, yq):
    ix = np.searchsorted(x_grid, xq) - 1
    iy = np.searchsorted(y_grid, yq) - 1
    ix = np.clip(ix, 0, len(x_grid) - 2)
    iy = np.clip(iy, 0, len(y_grid) - 2)
    x1 = x_grid[ix]
    x2 = x_grid[ix + 1]
    y1 = y_grid[iy]
    y2 = y_grid[iy + 1]
    tx = np.where(np.abs(x2 - x1) > 1e-12, (xq - x1) / (x2 - x1), 0.0)
    ty = np.where(np.abs(y2 - y1) > 1e-12, (yq - y1) / (y2 - y1), 0.0)
    z11 = z_arr[iy, ix]
    z12 = z_arr[iy + 1, ix]
    z21 = z_arr[iy, ix + 1]
    z22 = z_arr[iy + 1, ix + 1]
    return (1 - tx) * (1 - ty) * z11 + tx * (1 - ty) * z21 + (1 - tx) * ty * z12 + tx * ty * z22


def _extract_iso_segments(field, x_grid, y_grid, level):
    nx = len(x_grid)
    ny = len(y_grid)
    seg_x = []
    seg_y = []

    def interp(p1, p2, v1, v2):
        if abs(v2 - v1) < 1e-12:
            return ((p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5)
        t = (level - v1) / (v2 - v1)
        t = min(1.0, max(0.0, t))
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))

    for iy in range(ny - 1):
        y0 = y_grid[iy]
        y1 = y_grid[iy + 1]
        for ix in range(nx - 1):
            x0 = x_grid[ix]
            x1 = x_grid[ix + 1]

            v0 = field[iy, ix]
            v1v = field[iy, ix + 1]
            v2 = field[iy + 1, ix + 1]
            v3 = field[iy + 1, ix]

            if np.isnan(v0) or np.isnan(v1v) or np.isnan(v2) or np.isnan(v3):
                continue

            b0 = v0 >= level
            b1 = v1v >= level
            b2 = v2 >= level
            b3 = v3 >= level
            if (b0 == b1) and (b1 == b2) and (b2 == b3):
                continue

            p0 = (x0, y0)
            p1 = (x1, y0)
            p2 = (x1, y1)
            p3 = (x0, y1)

            pts = []
            if b0 != b1:
                pts.append(interp(p0, p1, v0, v1v))
            if b1 != b2:
                pts.append(interp(p1, p2, v1v, v2))
            if b2 != b3:
                pts.append(interp(p2, p3, v2, v3))
            if b3 != b0:
                pts.append(interp(p3, p0, v3, v0))

            if len(pts) == 2:
                seg_x.extend([pts[0][0], pts[1][0], None])
                seg_y.extend([pts[0][1], pts[1][1], None])
            elif len(pts) == 4:
                seg_x.extend([pts[0][0], pts[1][0], None, pts[2][0], pts[3][0], None])
                seg_y.extend([pts[0][1], pts[1][1], None, pts[2][1], pts[3][1], None])

    return np.asarray(seg_x, dtype=object), np.asarray(seg_y, dtype=object)


def _camera_from_preset(bounds, preset):
    scale = 1.10
    p = (preset or "isometric").lower()
    if p == "front":
        return dict(eye=dict(x=0.0, y=-2.15 * scale, z=0.0), up=dict(x=0, y=0, z=1), center=dict(x=0, y=0, z=0))
    if p == "back":
        return dict(eye=dict(x=0.0, y=2.15 * scale, z=0.0), up=dict(x=0, y=0, z=1), center=dict(x=0, y=0, z=0))
    if p == "left":
        return dict(eye=dict(x=-2.15 * scale, y=0.0, z=0.0), up=dict(x=0, y=0, z=1), center=dict(x=0, y=0, z=0))
    if p == "right":
        return dict(eye=dict(x=2.15 * scale, y=0.0, z=0.0), up=dict(x=0, y=0, z=1), center=dict(x=0, y=0, z=0))
    if p == "top":
        return dict(eye=dict(x=0.0, y=0.0, z=2.15 * scale), up=dict(x=0, y=1, z=0), center=dict(x=0, y=0, z=0))
    if p == "bottom":
        return dict(eye=dict(x=0.0, y=0.0, z=-2.15 * scale), up=dict(x=0, y=1, z=0), center=dict(x=0, y=0, z=0))
    return dict(eye=dict(x=-1.55 * scale, y=-1.45 * scale, z=0.95 * scale), up=dict(x=0, y=0, z=1), center=dict(x=0, y=0, z=0))


def _bbox_lines_trace(bounds):
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    pts = np.array(
        [
            [xmin, ymin, zmin],
            [xmax, ymin, zmin],
            [xmax, ymax, zmin],
            [xmin, ymax, zmin],
            [xmin, ymin, zmax],
            [xmax, ymin, zmax],
            [xmax, ymax, zmax],
            [xmin, ymax, zmax],
        ],
        dtype=float,
    )
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    x, y, z = [], [], []
    for a, b in edges:
        x.extend([pts[a, 0], pts[b, 0], None])
        y.extend([pts[a, 1], pts[b, 1], None])
        z.extend([pts[a, 2], pts[b, 2], None])
    return go.Scatter3d(x=x, y=y, z=z, mode="lines", line=dict(color="#00bcd4", width=4), hoverinfo="skip", showlegend=False)


def render_tablet_3d(mesh_data, params):
    hb = max(0.0, params.get("Hb", 2.54))
    x_grid = mesh_data["x_grid"]
    y_grid = mesh_data["y_grid"]
    z_top_grid = mesh_data["Z_cup_top"]
    z_bot_grid = mesh_data["Z"]

    theta = np.linspace(0, 2 * np.pi, 320)
    rr = np.linspace(0, 1, 160)
    rr_grid, tt_grid = np.meshgrid(rr, theta, indexing="ij")

    x_c, y_c = _shape_contour(params)
    r_boundary = _boundary_radius_from_contour(x_c, y_c, theta)
    r_grid = rr_grid * r_boundary[None, :]
    x_s = r_grid * np.cos(tt_grid)
    y_s = r_grid * np.sin(tt_grid)

    z_top_interp = _interp_bilinear(z_top_grid, x_grid, y_grid, x_s, y_s)
    z_bot_interp = _interp_bilinear(z_bot_grid, x_grid, y_grid, x_s, y_s)
    zt_s = z_top_interp + hb / 2
    zb_s = -z_bot_interp - hb / 2

    z_line = np.linspace(-hb / 2, hb / 2, 32)
    xb = np.tile(r_boundary * np.cos(theta), (len(z_line), 1))
    yb = np.tile(r_boundary * np.sin(theta), (len(z_line), 1))
    zb = np.tile(z_line[:, None], (1, len(theta)))

    cad_colorscale = [[0, "#db7b3b"], [1, "#db7b3b"]]
    vector_light = dict(x=-1, y=1, z=0.2)
    lighting_top = dict(ambient=0.4, diffuse=0.8, specular=0.3, roughness=0.6, fresnel=0.1)
    lighting_bot = dict(ambient=0.7, diffuse=0.4, specular=0.1, roughness=0.8, fresnel=0.2)

    render_mode = (params.get("render_mode", "shaded") or "shaded").lower()
    show_bbox = bool(params.get("show_bbox", False))
    view_preset = params.get("view_preset", "isometric")
    top_opacity, bottom_opacity, band_opacity = 1.0, 1.0, 1.0
    hide_surface = False
    if render_mode == "transparent":
        top_opacity, bottom_opacity, band_opacity = 0.55, 0.5, 0.5
    elif render_mode == "wireframe":
        hide_surface = True

    fig = go.Figure()
    fig.add_trace(
        go.Surface(
            x=x_s, y=y_s, z=zt_s, colorscale=cad_colorscale, showscale=False, hoverinfo="skip", name="Top",
            lighting=lighting_top, lightposition=vector_light, opacity=top_opacity, hidesurface=hide_surface,
        )
    )
    fig.add_trace(
        go.Surface(
            x=x_s, y=y_s, z=zb_s, colorscale=cad_colorscale, showscale=False, hoverinfo="skip", name="Bottom",
            lighting=lighting_bot, lightposition=vector_light, opacity=bottom_opacity, hidesurface=hide_surface,
        )
    )
    fig.add_trace(
        go.Surface(
            x=xb, y=yb, z=zb, colorscale=cad_colorscale, showscale=False, hoverinfo="skip", name="Band",
            lighting=lighting_bot, lightposition=vector_light, opacity=band_opacity, hidesurface=hide_surface,
        )
    )

    if render_mode in ("edges", "wireframe"):
        eps = max(1e-6, max(np.ptp(xb), np.ptp(yb), np.ptp(zt_s), np.ptp(zb_s)) * 0.0008)
        edge_line = dict(color="#101010", width=3)

        def add_edge(x_line, y_line, z_line, width=3):
            fig.add_trace(
                go.Scatter3d(
                    x=x_line, y=y_line, z=z_line, mode="lines",
                    line=dict(color="#101010", width=width), hoverinfo="skip", showlegend=False
                )
            )

        # 1) Outer transition lines: top<->band and bottom<->band
        add_edge(xb[0], yb[0], np.full_like(xb[0], hb / 2 + eps), width=3)
        add_edge(xb[0], yb[0], np.full_like(xb[0], -hb / 2 - eps), width=3)

        # 2) Inner land/cup transitions (top and bottom)
        xi, yi = _shape_contour_inner(params)
        z_top_i = _interp_bilinear(z_top_grid, x_grid, y_grid, xi, yi) + hb / 2
        z_bot_i = -_interp_bilinear(z_bot_grid, x_grid, y_grid, xi, yi) - hb / 2
        add_edge(xi, yi, z_top_i + eps, width=2)
        add_edge(xi, yi, z_bot_i - eps, width=2)

        # 2.1) FFBE: edge of the upper flat cup lid (Ref. Flat).
        profile_name = (params.get("profile", "") or "").lower()
        if profile_name in ("ffbe", "ffre"):
            dc = max(0.0, float(params.get("Dc", 0.0) or 0.0))
            if dc > 1e-6:
                lvl = max(0.0, dc - max(1e-4, dc * 1e-3))
                z_top_mask = np.where(mesh_data["mask_cup"], z_top_grid, np.nan)
                fx, fy = _extract_iso_segments(z_top_mask, x_grid, y_grid, level=lvl)
                if len(fx) > 0:
                    valid_f = np.array([v is not None for v in fx], dtype=bool)
                    xqf = fx[valid_f].astype(float)
                    yqf = fy[valid_f].astype(float)
                    zqf = _interp_bilinear(z_top_grid, x_grid, y_grid, xqf, yqf) + hb / 2
                    fz = np.full_like(fx, None, dtype=object)
                    fz[valid_f] = zqf + eps
                    add_edge(fx, fy, fz, width=2)

                # Bottom cup mirror line of the same flat lid boundary.
                z_bot_mask = np.where(mesh_data["mask_cup"], z_bot_grid, np.nan)
                bx, by = _extract_iso_segments(z_bot_mask, x_grid, y_grid, level=lvl)
                if len(bx) > 0:
                    valid_b = np.array([v is not None for v in bx], dtype=bool)
                    xqb = bx[valid_b].astype(float)
                    yqb = by[valid_b].astype(float)
                    zqb = -_interp_bilinear(z_bot_grid, x_grid, y_grid, xqb, yqb) - hb / 2
                    bz = np.full_like(bx, None, dtype=object)
                    bz[valid_b] = zqb - eps
                    add_edge(bx, by, bz, width=2)

        # 3) Groove feature lines (where groove intersects top face)
        z = mesh_data["Z"]
        z_g = mesh_data["Z_groove"]
        mask_cup = mesh_data["mask_cup"]
        diff = np.where(mask_cup, z - z_g, np.nan)
        groove_visible = np.where(mask_cup, (z_g < z - 1e-6) & (z_g > 1e-6), False)
        sx, sy = _extract_iso_segments(diff, x_grid, y_grid, level=0.0)
        if len(sx) > 0:
            valid = np.array([v is not None for v in sx], dtype=bool)
            xq = sx[valid].astype(float)
            yq = sy[valid].astype(float)
            zq = _interp_bilinear(z_top_grid, x_grid, y_grid, xq, yq) + hb / 2
            sz = np.full_like(sx, None, dtype=object)
            sz[valid] = zq + eps
            add_edge(sx, sy, sz, width=2)

        # 4) Inner tangent line of groove corner radius
        b_type = (params.get("b_type", "none") or "none").lower()
        b_depth = float(params.get("b_depth", 0.0) or 0.0)
        z_g_masked = np.where(mask_cup, z_g, np.nan)
        gx0, gy0 = _extract_iso_segments(z_g_masked, x_grid, y_grid, level=0.0)
        if len(gx0) > 0:
            valid0 = np.array([v is not None for v in gx0], dtype=bool)
            gz0 = np.full_like(gx0, None, dtype=object)
            gz0[valid0] = hb / 2 + eps
            add_edge(gx0, gy0, gz0, width=2)

        if b_type != "none" and b_depth > 0:
            b_angle = float(params.get("b_angle", 90.0) or 90.0)
            b_ri = float(params.get("b_Ri", 0.06) or 0.06)
            x_ti = b_ri * np.sin(np.radians(b_angle / 2.0))
            if x_ti > 1e-4:
                shape_name = params.get("shape", "round")
                cut_field = np.abs(mesh_data["Y"]) if shape_name == "round" else np.abs(mesh_data["X"])
                # Draw inner groove radius/vee transition only where groove is actually visible.
                ti_field = np.where(groove_visible, cut_field - x_ti, np.nan)
                tx, ty = _extract_iso_segments(ti_field, x_grid, y_grid, level=0.0)
                if len(tx) > 0:
                    valid_t = np.array([v is not None for v in tx], dtype=bool)
                    xqt = tx[valid_t].astype(float)
                    yqt = ty[valid_t].astype(float)
                    zqt = _interp_bilinear(z_top_grid, x_grid, y_grid, xqt, yqt) + hb / 2
                    tz = np.full_like(tx, None, dtype=object)
                    tz[valid_t] = zqt + eps
                    add_edge(tx, ty, tz, width=2)

    x_min, x_max = float(np.nanmin(xb)), float(np.nanmax(xb))
    y_min, y_max = float(np.nanmin(yb)), float(np.nanmax(yb))
    z_min, z_max = float(np.nanmin(zb_s)), float(np.nanmax(zt_s))
    bounds = [x_min, x_max, y_min, y_max, z_min, z_max]
    camera = _camera_from_preset(bounds, view_preset)

    bbox_annotations = None
    if show_bbox:
        fig.add_trace(_bbox_lines_trace(bounds))
        bbox_annotations = [
            dict(
                x=x_max,
                y=y_min,
                z=z_min,
                text=f"X = {x_max - x_min:.1f} mm",
                showarrow=False,
                font=dict(color="#111111", size=14),
                xanchor="left",
                yanchor="middle",
            ),
            dict(
                x=x_min,
                y=y_max,
                z=z_min,
                text=f"Y = {y_max - y_min:.1f} mm",
                showarrow=False,
                font=dict(color="#111111", size=14),
                xanchor="left",
                yanchor="middle",
            ),
            dict(
                x=x_min,
                y=y_min,
                z=z_max,
                text=f"Z = {z_max - z_min:.1f} mm",
                showarrow=False,
                font=dict(color="#111111", size=14),
                xanchor="left",
                yanchor="bottom",
            ),
        ]

    base_axis_cfg = dict(visible=False, showgrid=False, zeroline=False, showspikes=False, showbackground=False)
    scene_config = dict(
        xaxis=dict(**base_axis_cfg),
        yaxis=dict(**base_axis_cfg),
        zaxis=dict(**base_axis_cfg),
        aspectmode="data",
        camera=camera,
        dragmode="orbit",
    )

    # Unified framing for all views/presets to keep scale and centering consistent.
    span_max = max(x_max - x_min, y_max - y_min, z_max - z_min)
    half = 0.5 * span_max * 1.04
    scene_config["xaxis"].update(range=[-half, half], autorange=False)
    scene_config["yaxis"].update(range=[-half, half], autorange=False)
    scene_config["zaxis"].update(range=[-half, half], autorange=False)
    scene_config["aspectmode"] = "cube"
    if bbox_annotations is not None:
        scene_config["annotations"] = bbox_annotations

    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=10),
        scene=scene_config,
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        hovermode=False,
    )
    return fig
