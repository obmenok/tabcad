import numpy as np
import plotly.graph_objects as go

from core.domain.shapes import shape_params


def _get_circle_contour(radius, density=220):
    t = np.linspace(0, 2 * np.pi, density)
    return radius * np.cos(t), radius * np.sin(t)


def _get_capsule_contour(l_val, w_val, density=150):
    r = w_val / 2
    l_flat = max(0, l_val - w_val)
    
    # 1. Правая дуга
    t_right = np.linspace(0, np.pi, density)
    x_right = l_flat / 2 + r * np.sin(t_right)
    y_right = r * np.cos(t_right)
    
    # 2. Нижняя прямая (плоская грань)
    x_bottom = np.linspace(l_flat / 2, -l_flat / 2, density)
    y_bottom = np.full_like(x_bottom, -r)
    
    # 3. Левая дуга
    t_left = np.linspace(np.pi, 2 * np.pi, density)
    x_left = -l_flat / 2 + r * np.sin(t_left)
    y_left = r * np.cos(t_left)
    
    # 4. Верхняя прямая (плоская грань)
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

    return (
        (1 - tx) * (1 - ty) * z11
        + tx * (1 - ty) * z21
        + (1 - tx) * ty * z12
        + tx * ty * z22
    )


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


def _shrink_xy(x_line, y_line, delta):
    if delta <= 0:
        return x_line, y_line
    r = np.hypot(x_line, y_line)
    scale = np.ones_like(r)
    mask = r > 1e-9
    scale[mask] = np.maximum(0.0, (r[mask] - delta) / r[mask])
    return x_line * scale, y_line * scale


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

    # Sketch style
    cad_colorscale = [[0, "#f3f3f3"], [1, "#d9d9d9"]]
    vector_light = dict(x=-0.8, y=0.9, z=0.4)
    lighting_top = dict(ambient=0.35, diffuse=0.85, specular=0.06, roughness=0.9, fresnel=0.03)
    lighting_bot = dict(ambient=0.28, diffuse=0.75, specular=0.04, roughness=0.92, fresnel=0.03)

    fig = go.Figure()
    fig.add_trace(
        go.Surface(
            x=x_s, y=y_s, z=zt_s,
            colorscale=cad_colorscale, showscale=False, hoverinfo="skip", name="Top",
            lighting=lighting_top, lightposition=vector_light, opacity=1.0
        )
    )
    fig.add_trace(
        go.Surface(
            x=x_s, y=y_s, z=zb_s,
            colorscale=cad_colorscale, showscale=False, hoverinfo="skip", name="Bottom",
            lighting=lighting_bot, lightposition=vector_light, opacity=1.0
        )
    )
    fig.add_trace(
        go.Surface(
            x=xb, y=yb, z=zb,
            colorscale=cad_colorscale, showscale=False, hoverinfo="skip", name="Band",
            lighting=lighting_bot, lightposition=vector_light, opacity=1.0
        )
    )

    edge_color = "#111111"
    max_span = max(float(np.max(np.abs(x_grid))), float(np.max(np.abs(y_grid))), 1.0)
    edge_inset = 0.001 * max_span
    z_eps = 0.0015 * max_span

    def add_line(x_line, y_line, z_line, width=3, color=edge_color):
        fig.add_trace(
            go.Scatter3d(
                x=x_line,
                y=y_line,
                z=z_line,
                mode="lines",
                line=dict(color=color, width=width),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    xo, yo = _shape_contour(params)
    xo_in, yo_in = _shrink_xy(xo, yo, edge_inset)
    add_line(xo_in, yo_in, np.full_like(xo_in, hb / 2 + z_eps), width=4)
    add_line(xo_in, yo_in, np.full_like(xo_in, -hb / 2 - z_eps), width=4)

    xi, yi = _shape_contour_inner(params)
    xi_in, yi_in = _shrink_xy(xi, yi, edge_inset * 0.4)
    zc = _interp_bilinear(z_top_grid, x_grid, y_grid, xi_in, yi_in) + hb / 2
    add_line(xi_in, yi_in, zc + z_eps, width=3)
    add_line(xi_in, yi_in, -zc - z_eps, width=3)

    b_type = (params.get("b_type", "none") or "none").lower()
    b_depth = float(params.get("b_depth", 0.0) or 0.0)
    if b_type != "none" and b_depth > 0:
        z = mesh_data["Z"]
        z_g = mesh_data["Z_groove"]
        mask_cup = mesh_data["mask_cup"]
        diff = np.where(mask_cup, z - z_g, np.nan)
        sx, sy = _extract_iso_segments(diff, x_grid, y_grid, level=0.0)
        if len(sx) > 0:
            valid = np.array([v is not None for v in sx], dtype=bool)
            xq = sx[valid].astype(float)
            yq = sy[valid].astype(float)
            zq = _interp_bilinear(z_top_grid, x_grid, y_grid, xq, yq) + hb / 2
            sz = np.full_like(sx, None, dtype=object)
            sz[valid] = zq
            add_line(sx, sy, sz, width=3)

        b_angle = float(params.get("b_angle", 90.0) or 90.0)
        b_ri = float(params.get("b_Ri", 0.06) or 0.06)
        x_ti = b_ri * np.sin(np.radians(b_angle / 2.0))
        if x_ti > 1e-4:
            shape_name = params.get("shape", "round")
            cut_field = np.abs(mesh_data["Y"]) if shape_name == "round" else np.abs(mesh_data["X"])
            ti_field = np.where(mask_cup, cut_field - x_ti, np.nan)
            tx, ty = _extract_iso_segments(ti_field, x_grid, y_grid, level=0.0)
            if len(tx) > 0:
                valid_t = np.array([v is not None for v in tx], dtype=bool)
                xqt = tx[valid_t].astype(float)
                yqt = ty[valid_t].astype(float)
                zqt = _interp_bilinear(z_top_grid, x_grid, y_grid, xqt, yqt) + hb / 2
                tz = np.full_like(tx, None, dtype=object)
                tz[valid_t] = zqt
                add_line(tx, ty, tz, width=2)

    z_top_mask = np.where(mesh_data["mask_cup"], z_top_grid, np.nan)
    z_bot_mask = np.where(mesh_data["mask_cup"], z_bot_grid, np.nan)
    top_max = float(np.nanmax(z_top_mask)) if np.any(np.isfinite(z_top_mask)) else 0.0
    bot_max = float(np.nanmax(z_bot_mask)) if np.any(np.isfinite(z_bot_mask)) else 0.0
    if top_max > 1e-5:
        for lv in np.linspace(top_max * 0.3, top_max * 0.85, 3):
            sx, sy = _extract_iso_segments(z_top_mask, x_grid, y_grid, level=lv)
            if len(sx) == 0:
                continue
            sz = np.full_like(sx, None, dtype=object)
            valid = np.array([v is not None for v in sx], dtype=bool)
            sz[valid] = lv + hb / 2
            add_line(sx, sy, sz, width=1, color="#2e2e2e")
    if bot_max > 1e-5:
        for lv in np.linspace(bot_max * 0.35, bot_max * 0.8, 2):
            sx, sy = _extract_iso_segments(z_bot_mask, x_grid, y_grid, level=lv)
            if len(sx) == 0:
                continue
            sz = np.full_like(sx, None, dtype=object)
            valid = np.array([v is not None for v in sx], dtype=bool)
            sz[valid] = -lv - hb / 2
            add_line(sx, sy, sz, width=1, color="#2e2e2e")

    for a in np.linspace(0, 2 * np.pi, 6, endpoint=False):
        rb = _boundary_radius_from_contour(x_c, y_c, np.array([a]))[0]
        xv = np.full_like(z_line, rb * np.cos(a))
        yv = np.full_like(z_line, rb * np.sin(a))
        add_line(xv, yv, z_line, width=1, color="#2e2e2e")

    shape, _, w_val, l_val, _, _, _ = shape_params(params)
    if shape == "round":
        r_lim = max(w_val, l_val) / 2 + 1.0
        z_lim = hb / 2 + max(float(np.nanmax(z_top_grid)), float(np.nanmax(z_bot_grid))) + 1.0
        scene_config = dict(
            xaxis=dict(title="X (mm)", range=[-r_lim, r_lim], showbackground=False),
            yaxis=dict(title="Y (mm)", range=[-r_lim, r_lim], showbackground=False),
            zaxis=dict(title="Z (mm)", range=[-z_lim, z_lim], showbackground=False),
            aspectmode="manual",
            aspectratio=dict(x=1, y=1, z=0.55),
            camera=dict(eye=dict(x=1.6, y=1.4, z=0.9)),
        )
    else:
        scene_config = dict(
            xaxis=dict(title="X (mm)", showbackground=False),
            yaxis=dict(title="Y (mm)", showbackground=False),
            zaxis=dict(title="Z (mm)", showbackground=False),
            aspectmode="data",
            camera=dict(eye=dict(x=1.6, y=1.4, z=0.9)),
        )

    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=10),
        scene=scene_config,
        paper_bgcolor="#f5f5f5",
        plot_bgcolor="#f5f5f5",
        showlegend=False,
    )
    return fig
