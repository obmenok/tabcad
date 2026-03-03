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
        fig.add_trace(go.Scatter3d(x=xb[0], y=yb[0], z=np.full_like(xb[0], zt_s.max() + eps), mode="lines", line=edge_line, hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter3d(x=xb[0], y=yb[0], z=np.full_like(xb[0], zb_s.min() - eps), mode="lines", line=edge_line, hoverinfo="skip", showlegend=False))

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
