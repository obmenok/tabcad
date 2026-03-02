import numpy as np
import dash_vtk

from core.renderer_3d import _boundary_radius_from_contour, _interp_bilinear, _shape_contour


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


def render_tablet_3d_vtk(mesh_data, params):
    hb = max(0.0, params.get("Hb", 2.54))
    x_grid = mesh_data["x_grid"]
    y_grid = mesh_data["y_grid"]
    z_top_grid = mesh_data["Z_cup_top"]
    z_bot_grid = mesh_data["Z"]

    theta = np.linspace(0, 2 * np.pi, 220)
    rr = np.linspace(0, 1, 120)
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

    z_line = np.linspace(-hb / 2, hb / 2, 40)
    xb = np.tile(r_boundary[None, :] * np.cos(theta)[None, :], (len(z_line), 1))
    yb = np.tile(r_boundary[None, :] * np.sin(theta)[None, :], (len(z_line), 1))
    zband = np.tile(z_line[:, None], (1, len(theta)))

    p_top, polys_top = _grid_to_polydata(x_s, y_s, zt_s)
    p_bot, polys_bot = _grid_to_polydata(x_s, y_s, zb_s)
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
