import base64
import io

import numpy as np
import plotly.graph_objects as go
import pyvista as pv
from PIL import Image

from core.renderer_3d import _boundary_radius_from_contour, _interp_bilinear, _shape_contour


def _to_structured(x, y, z):
    grid = pv.StructuredGrid()
    grid.points = np.c_[x.ravel(order="F"), y.ravel(order="F"), z.ravel(order="F")]
    grid.dimensions = [x.shape[0], x.shape[1], 1]
    return grid


def _image_to_figure(img):
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    fig = go.Figure()
    fig.add_layout_image(
        dict(
            source=f"data:image/png;base64,{b64}",
            xref="x",
            yref="y",
            x=0,
            y=1,
            sizex=1,
            sizey=1,
            sizing="stretch",
            layer="below",
        )
    )
    fig.update_xaxes(visible=False, range=[0, 1], fixedrange=True)
    fig.update_yaxes(visible=False, range=[0, 1], fixedrange=True, scaleanchor="x")
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="white",
        plot_bgcolor="white",
        dragmode=False,
    )
    return fig


def render_tablet_3d_cad(mesh_data, params, window_size=(900, 900)):
    hb = max(0.0, params.get("Hb", 2.54))
    x_grid = mesh_data["x_grid"]
    y_grid = mesh_data["y_grid"]
    z_top_grid = mesh_data["Z_cup_top"]
    z_bot_grid = mesh_data["Z"]

    theta = np.linspace(0, 2 * np.pi, 240)
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
    zb = np.tile(z_line[:, None], (1, len(theta)))

    top = _to_structured(x_s, y_s, zt_s)
    bottom = _to_structured(x_s, y_s, zb_s)
    band = _to_structured(xb, yb, zb)

    pl = pv.Plotter(off_screen=True, window_size=window_size)
    pl.set_background("#f2f2f2")
    pl.enable_lightkit()

    # SolidWorks-like matte plastics/metal look
    pl.add_mesh(top, color="#d6dbe3", smooth_shading=True, pbr=True, metallic=0.05, roughness=0.35)
    pl.add_mesh(bottom, color="#b8bec8", smooth_shading=True, pbr=True, metallic=0.05, roughness=0.45)
    pl.add_mesh(band, color="#c7cdd6", smooth_shading=True, pbr=True, metallic=0.08, roughness=0.40)

    shell = top.extract_surface().merge(bottom.extract_surface()).merge(band.extract_surface())
    edges = shell.extract_feature_edges(
        boundary_edges=True,
        feature_edges=True,
        manifold_edges=False,
        non_manifold_edges=False,
        feature_angle=35.0,
    )
    pl.add_mesh(edges, color="black", line_width=1.1)

    pl.view_isometric()
    pl.camera.zoom(1.2)
    img = pl.screenshot(return_img=True)
    pl.close()

    return _image_to_figure(img)
