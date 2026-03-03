import numpy as np
import dash_vtk

from core.renderer_3d import _boundary_radius_from_contour, _interp_bilinear, _shape_contour
from core.domain.profiles import eval_profile_1d
from core.domain.shapes import capsule_rho, minor_span, oval_mask, shape_params


def _grid_to_polydata(x, y, z):
    nr, nt = x.shape
    points = np.column_stack((x.ravel(), y.ravel(), z.ravel())).astype(np.float32)

    polys = []
    for i in range(nr - 1):
        row = i * nt
        next_row = (i + 1) * nt
        for j in range(nt - 1):
            p0 = row + j
            p1 = row + j + 1
            p2 = next_row + j + 1
            p3 = next_row + j
            polys.extend([3, p0, p1, p2, 3, p0, p2, p3])
    return points, np.asarray(polys, dtype=np.int32)


def _grid_to_polydata_masked(x, y, z, mask):
    ny, nx = z.shape
    points = np.column_stack((x.ravel(), y.ravel(), z.ravel())).astype(np.float32)

    polys = []
    for iy in range(ny - 1):
        row = iy * nx
        next_row = (iy + 1) * nx
        for ix in range(nx - 1):
            if not (mask[iy, ix] and mask[iy, ix + 1] and mask[iy + 1, ix + 1] and mask[iy + 1, ix]):
                continue
            p0 = row + ix
            p1 = row + ix + 1
            p2 = next_row + ix + 1
            p3 = next_row + ix
            polys.extend([3, p0, p1, p2, 3, p0, p2, p3])
    return points, np.asarray(polys, dtype=np.int32)


def _face_mask(params, x_grid, y_grid):
    shape, is_modified, w_val, l_val, _, re, rs = shape_params(params)
    x_arr, y_arr = np.meshgrid(x_grid, y_grid)

    if shape == "round":
        return (x_arr**2 + y_arr**2) <= (w_val / 2) ** 2

    if shape == "capsule" and not is_modified:
        l_flat = max(0.0, l_val - w_val)
        return capsule_rho(x_arr, y_arr, l_flat) <= (w_val / 2)

    return oval_mask(x_arr, y_arr, l_val, w_val, re, rs)


def _round_top_surface_direct(params, x_s, y_s):
    _, _, w_val, _, land, _, _ = shape_params(params)
    dc = max(0.0, float(params.get("Dc", 1.5) or 1.5))
    rc = max(0.001, w_val / 2 - land)

    rho = np.sqrt(x_s**2 + y_s**2)
    z = np.zeros_like(x_s)
    mask_cup = rho <= rc
    z[mask_cup] = eval_profile_1d(rho[mask_cup], params, rc, dc)

    b_type = (params.get("b_type", "none") or "none").lower()
    b_depth = float(params.get("b_depth", 0.0) or 0.0)
    if b_type == "none" or b_depth <= 0:
        return z

    b_angle = float(params.get("b_angle", 90.0) or 90.0)
    b_ri = float(params.get("b_Ri", 0.061) or 0.061)
    alpha = np.radians(b_angle / 2.0)
    if alpha <= 1e-9:
        return z

    d_sharp = b_ri / np.sin(alpha) - b_ri if b_ri > 0 else 0.0
    x_ti = b_ri * np.sin(alpha)

    cut_axis = np.abs(y_s)
    along_axis = np.abs(x_s)
    span = minor_span(params)
    z_centerline = eval_profile_1d(along_axis, params, span, dc)

    if b_type == "standard":
        z_bottom = z_centerline - b_depth
    elif b_type == "cut_through":
        z_bottom = np.full_like(z, dc - b_depth)
    elif b_type == "decreasing":
        z_bottom = z_centerline - b_depth * np.maximum(0, 1 - (along_axis / max(1e-6, span)) ** 2)
    else:
        z_bottom = z_centerline - b_depth

    z_v = z_bottom - d_sharp + cut_axis / np.tan(alpha)
    z_inner = z_bottom + b_ri - np.sqrt(np.maximum(0, b_ri**2 - cut_axis**2))
    z_groove = np.where(cut_axis <= x_ti, z_inner, z_v)
    return np.maximum(0, np.minimum(z, z_groove))


def render_tablet_3d_vtk(mesh_data, params):
    hb = max(0.0, params.get("Hb", 2.54))
    x_grid = mesh_data["x_grid"]
    y_grid = mesh_data["y_grid"]
    z_top_grid = mesh_data["Z_cup_top"]
    z_bot_grid = mesh_data["Z"]

    shape, _, _, _, _, _, _ = shape_params(params)
    b_type = (params.get("b_type", "none") or "none").lower()
    b_depth = float(params.get("b_depth", 0.0) or 0.0)
    has_bisect = b_type != "none" and b_depth > 0
    theta_n = 720 if (shape == "round" and has_bisect) else 360
    theta = np.linspace(0, 2 * np.pi, theta_n)

    x_c, y_c = _shape_contour(params)
    r_boundary = _boundary_radius_from_contour(x_c, y_c, theta)

    z_line = np.linspace(-hb / 2, hb / 2, 40)
    xb = np.tile(r_boundary[None, :] * np.cos(theta)[None, :], (len(z_line), 1))
    yb = np.tile(r_boundary[None, :] * np.sin(theta)[None, :], (len(z_line), 1))
    zband = np.tile(z_line[:, None], (1, len(theta)))

    if shape == "round":
        rr_n = 320 if has_bisect else 220
        rr = np.linspace(0, 1, rr_n)
        rr_grid, tt_grid = np.meshgrid(rr, theta, indexing="ij")
        r_grid = rr_grid * r_boundary[None, :]
        x_s = r_grid * np.cos(tt_grid)
        y_s = r_grid * np.sin(tt_grid)
        z_top_interp = _round_top_surface_direct(params, x_s, y_s)
        z_bot_interp = _interp_bilinear(z_bot_grid, x_grid, y_grid, x_s, y_s)
        zt_s = z_top_interp + hb / 2
        zb_s = -z_bot_interp - hb / 2
        p_top, polys_top = _grid_to_polydata(x_s, y_s, zt_s)
        p_bot, polys_bot = _grid_to_polydata(x_s, y_s, zb_s)
    else:
        x_arr, y_arr = np.meshgrid(x_grid, y_grid)
        mask_face = _face_mask(params, x_grid, y_grid)
        zt_grid = z_top_grid + hb / 2
        zb_grid = -z_bot_grid - hb / 2
        p_top, polys_top = _grid_to_polydata_masked(x_arr, y_arr, zt_grid, mask_face)
        p_bot, polys_bot = _grid_to_polydata_masked(x_arr, y_arr, zb_grid, mask_face)
    p_band, polys_band = _grid_to_polydata(xb, yb, zband)

    return dash_vtk.View(
        id="vtk-view",
        background=[0.95, 0.95, 0.95],
        cameraPosition=[1.5, -1.8, 1.2],
        cameraViewUp=[0, 0, 1],
        children=[
            dash_vtk.GeometryRepresentation(
                property={"color": [0.84, 0.86, 0.90], "specular": 0.15, "diffuse": 0.9, "ambient": 0.15},
                children=[dash_vtk.PolyData(points=p_top.ravel().tolist(), polys=polys_top.ravel().tolist())],
            ),
            dash_vtk.GeometryRepresentation(
                property={"color": [0.73, 0.76, 0.81], "specular": 0.08, "diffuse": 0.85, "ambient": 0.18},
                children=[dash_vtk.PolyData(points=p_bot.ravel().tolist(), polys=polys_bot.ravel().tolist())],
            ),
            dash_vtk.GeometryRepresentation(
                property={"color": [0.78, 0.81, 0.86], "specular": 0.1, "diffuse": 0.88, "ambient": 0.17},
                children=[dash_vtk.PolyData(points=p_band.ravel().tolist(), polys=polys_band.ravel().tolist())],
            ),
        ],
        style={"width": "100%", "height": "100%"},
    )
