import base64
from io import BytesIO
import os
import re

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib import font_manager
from matplotlib.colors import to_rgb
from types import SimpleNamespace

from core.engine import get_1d_z_engine, get_compound_profile

# Web style - minimal config, most values are hardcoded in the drawing functions
WEB_STYLE = {
    "dim_line_width": 0.6,
    "text_color": "#9467bd",
}

# ISO PDF style with configurable dimension presentation
ISO_PDF_STYLE = {
    # Line widths (matplotlib points, 1 pt ≈ 0.35 mm)
    "dim_line_width": 0.72,       # Dimension line thickness
    "ext_line_width": 0.72,       # Extension line thickness
    
    # Text settings
    "text_color": "#000000",      # Dimension text color
    "text_font_size": 12,         # Dimension text size in points
    "text_gap_from_dim_line": 0.4, # Distance from text to dimension line
    "text_bbox_pad": 0.2,         # Padding around text background box
    
    # Extension line settings
    "ext_line_gap_from_feature": 0.0,  # Gap between feature edge and extension line start
    "ext_line_overrun": 0.5,      # How far extension line extends past dimension line
    
    # Arrow settings (data units)
    "arrow_length": 1.0,           # Arrow head length
    "arrow_width": 0.3,            # Arrow head width
    
    # Text positioning
    "outside_text_dist": 4.0,           # Length of right tail for external dimensions
    "outside_text_offset_ratio": 0.7,   # Text position as fraction of outside_text_dist
}

# Global state (set in render_tablet based on selected style)
DIM_LINE_WIDTH = WEB_STYLE["dim_line_width"]
C_TEXT = WEB_STYLE["text_color"]
EXT_LINE_WIDTH = ISO_PDF_STYLE["ext_line_width"]
TEXT_FONT_SIZE = ISO_PDF_STYLE["text_font_size"]
TEXT_GAP_FROM_DIM_LINE = ISO_PDF_STYLE["text_gap_from_dim_line"]
TEXT_BBOX_PAD = ISO_PDF_STYLE["text_bbox_pad"]
EXT_LINE_GAP_FROM_FEATURE = ISO_PDF_STYLE["ext_line_gap_from_feature"]
EXT_LINE_OVERRUN = ISO_PDF_STYLE["ext_line_overrun"]
OUTSIDE_TEXT_DIST = ISO_PDF_STYLE["outside_text_dist"]
OUTSIDE_TEXT_OFFSET_RATIO = ISO_PDF_STYLE["outside_text_offset_ratio"]
ARROW_LENGTH = ISO_PDF_STYLE["arrow_length"]
ARROW_WIDTH = ISO_PDF_STYLE["arrow_width"]
ISO_PDF_ACTIVE = False
PDF_FONT_PROPERTIES = None

# Load osifont for ISO PDF drawings
_OSIFONT_PATH = os.path.join("assets", "osifont.ttf")
if os.path.exists(_OSIFONT_PATH):
    try:
        font_manager.fontManager.addfont(_OSIFONT_PATH)
        PDF_FONT_PROPERTIES = font_manager.FontProperties(fname=_OSIFONT_PATH)
    except Exception as e:
        print(f"Warning: Failed to load osifont: {e}")
        PDF_FONT_PROPERTIES = None


_REQUIRED_PARAM_KEYS = [
    "shape",
    "is_modified",
    "W",
    "L",
    "Re",
    "Rs",
    "Land",
    "Hb",
    "Dc",
    "Tt",
    "profile",
    "b_type",
    "b_depth",
    "b_double_sided",
    "b_cruciform",
    "b_angle",
    "b_Ri",
    "Bev_A",
    "Bev_D",
    "R_edge",
    "Blend_R",
    "R_maj_maj",
    "R_maj_min",
    "R_min_maj",
    "R_min_min",
    "Rc_min",
    "Rc_maj",
    "render_2d_shaded",
]


def _validate_params(params):
    missing = [k for k in _REQUIRED_PARAM_KEYS if k not in params or params[k] is None]
    if missing:
        raise ValueError(f"Отсутствует параметр(ы): {', '.join(missing)}")
    return SimpleNamespace(**params)


def _draw_shaded_polygon(ax, x_poly, y_poly, base_rgb=(0.86, 0.78, 0.73), alpha=1.0, rotate_90=False):
    x = np.asarray(x_poly, dtype=float)
    y = np.asarray(y_poly, dtype=float)
    if len(x) < 3 or len(y) < 3:
        return
    if not (np.isclose(x[0], x[-1]) and np.isclose(y[0], y[-1])):
        x = np.append(x, x[0])
        y = np.append(y, y[0])

    verts = np.column_stack([x, y])
    codes = np.full(len(verts), Path.LINETO, dtype=np.uint8)
    codes[0] = Path.MOVETO
    codes[-1] = Path.CLOSEPOLY
    patch = PathPatch(Path(verts, codes), facecolor="none", edgecolor="none", transform=ax.transData)
    ax.add_patch(patch)

    xmin, xmax = float(np.min(x)), float(np.max(x))
    ymin, ymax = float(np.min(y)), float(np.max(y))
    if xmax - xmin < 1e-6 or ymax - ymin < 1e-6:
        return

    nx, ny = 260, 260
    xx = np.linspace(xmin, xmax, nx)
    yy = np.linspace(ymin, ymax, ny)
    X, Y = np.meshgrid(xx, yy)

    xn = 2.0 * (X - xmin) / (xmax - xmin) - 1.0
    yn = 2.0 * (Y - ymin) / (ymax - ymin) - 1.0
    if rotate_90:
        # Rotate shading frame 90 degrees clockwise.
        xr = yn
        yr = -xn
    else:
        xr = xn
        yr = yn

    light = 0.62 - 0.26 * xr + 0.18 * yr
    spec = np.exp(-((xr + 0.15) ** 2 / 0.05 + (yr - 0.1) ** 2 / 0.2))
    shade = np.clip(light + 0.25 * spec, 0.0, 1.0)

    base = np.array(base_rgb, dtype=float).reshape(1, 1, 3)
    rgb = np.clip(base * (0.74 + 0.46 * shade[:, :, None]), 0.0, 1.0)
    rgba = np.dstack([rgb, np.full((ny, nx), alpha)])

    im = ax.imshow(
        rgba,
        extent=[xmin, xmax, ymin, ymax],
        origin="lower",
        interpolation="bilinear",
        zorder=0.2,
    )
    im.set_clip_path(patch)


def _draw_solid_polygon(ax, x_poly, y_poly, color="#dec9bd", alpha=0.95, zorder=0.35):
    x = np.asarray(x_poly, dtype=float)
    y = np.asarray(y_poly, dtype=float)
    if len(x) < 3 or len(y) < 3:
        return
    if not (np.isclose(x[0], x[-1]) and np.isclose(y[0], y[-1])):
        x = np.append(x, x[0])
        y = np.append(y, y[0])
    ax.fill(x, y, color=color, alpha=alpha, linewidth=0, zorder=zorder)


def _safe_unit(vx, vy):
    dist = np.hypot(vx, vy)
    if dist <= 1e-12:
        return 0.0, 0.0
    return vx / dist, vy / dist


def _format_dim_text(text):
    """Format dimension text for ISO PDF: add prefixes, format numbers."""
    if not ISO_PDF_ACTIVE:
        return text
    raw = str(text or "")
    
    # Determine prefix based on text content
    prefix = ""
    if "Diameter" in raw:
        prefix = "\u2300"  # Diameter sign ⌀
    elif "Radius" in raw:
        prefix = "R"
    
    # Extract numeric value
    m = re.search(r"[-+]?\d+(?:[.,]\d+)?", raw)
    if not m:
        return raw
    token = m.group(0).replace(",", ".")
    try:
        val = float(token)
    except ValueError:
        return raw
    
    # Format number: 2 decimal places, remove trailing zeros
    out = f"{val:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    
    # Add degree sign if present in original
    if "°" in raw:
        out += "°"
    
    # Return with prefix
    return f"{prefix}{out}" if prefix else out


def _extension_segment(p0x, p0y, p1x, p1y):
    ux, uy = _safe_unit(p1x - p0x, p1y - p0y)
    sx = p0x + ux * EXT_LINE_GAP_FROM_FEATURE
    sy = p0y + uy * EXT_LINE_GAP_FROM_FEATURE
    ex = p1x + ux * EXT_LINE_OVERRUN
    ey = p1y + uy * EXT_LINE_OVERRUN
    return sx, sy, ex, ey


def _dim_text_kwargs():
    kwargs = {"fontsize": TEXT_FONT_SIZE}
    if ISO_PDF_ACTIVE and PDF_FONT_PROPERTIES is not None:
        kwargs["fontproperties"] = PDF_FONT_PROPERTIES
    return kwargs


def _draw_arrowhead(ax, tip_x, tip_y, out_x, out_y, length=None, width=None):
    """
    Draw arrowhead as a filled triangle.
    Arrow orientation is computed from tip -> outer point vector.
    tip_x, tip_y: position of arrow tip (touches extension line or profile)
    out_x, out_y: point in direction arrow points (away from tip)
    length, width: arrow dimensions (default from global ARROW_LENGTH, ARROW_WIDTH)
    """
    if length is None:
        length = ARROW_LENGTH
    if width is None:
        width = ARROW_WIDTH
    
    ux, uy = _safe_unit(out_x - tip_x, out_y - tip_y)
    if abs(ux) < 1e-12 and abs(uy) < 1e-12:
        return
    bx = tip_x + ux * length
    by = tip_y + uy * length
    nx, ny = -uy, ux
    hw = width / 2.0
    points = np.array(
        [
            [tip_x, tip_y],
            [bx + nx * hw, by + ny * hw],
            [bx - nx * hw, by - ny * hw],
        ]
    )
    ax.add_patch(
        Polygon(
            points,
            closed=True,
            facecolor="black",
            edgecolor="black",
            linewidth=0,
            antialiased=False,
            joinstyle="miter",
            zorder=5,
        )
    )


def draw_ext(ax, px1, py1, px2, py2, dx, dy, text, offset=(0, 0)):
    """Draw internal dimension (arrows inside extension lines)."""
    text = _format_dim_text(text)
    ex1, ey1 = px1 + dx, py1 + dy
    ex2, ey2 = px2 + dx, py2 + dy
    
    if not ISO_PDF_ACTIVE:
        # Original web style - uses matplotlib annotate
        sgx = np.sign(dx) if dx != 0 else 0
        sgy = np.sign(dy) if dy != 0 else 0
        ax.plot([px1, ex1 + sgx * 0.5], [py1, ey1 + sgy * 0.5], "k-", lw=DIM_LINE_WIDTH)
        ax.plot([px2, ex2 + sgx * 0.5], [py2, ey2 + sgy * 0.5], "k-", lw=DIM_LINE_WIDTH)
        ax.annotate(
            "",
            xy=(ex1, ey1),
            xytext=(ex2, ey2),
            arrowprops=dict(arrowstyle="<|-|>,head_length=1,head_width=0.175", color="black", lw=DIM_LINE_WIDTH, mutation_scale=10.0),
        )
        ax.text(
            (ex1 + ex2) / 2 + offset[0],
            (ey1 + ey2) / 2 + offset[1],
            text,
            color=C_TEXT,
            ha="center",
            va="center",
            bbox=dict(facecolor="#ffffff", edgecolor="none", pad=1),
            fontsize=9,
        )
        return

    # ISO PDF style - arrows touch extension lines exactly
    # Draw extension lines
    s1x, s1y, e1x, e1y = _extension_segment(px1, py1, ex1, ey1)
    s2x, s2y, e2x, e2y = _extension_segment(px2, py2, ex2, ey2)
    ax.plot([s1x, e1x], [s1y, e1y], "k-", lw=EXT_LINE_WIDTH)
    ax.plot([s2x, e2x], [s2y, e2y], "k-", lw=EXT_LINE_WIDTH)

    # Compute direction vector
    vec_x, vec_y = ex2 - ex1, ey2 - ey1
    dist = np.hypot(vec_x, vec_y)
    if dist <= 1e-12:
        return
    ux, uy = vec_x / dist, vec_y / dist
    
    # Draw dimension line (stops before arrow tips)
    ax.plot([ex1 + ux * ARROW_LENGTH, ex2 - ux * ARROW_LENGTH], 
            [ey1 + uy * ARROW_LENGTH, ey2 - uy * ARROW_LENGTH], "k-", lw=DIM_LINE_WIDTH)
    
    # Draw arrowheads with tips at extension line positions
    _draw_arrowhead(ax, ex1, ey1, ex1 + ux * ARROW_LENGTH, ey1 + uy * ARROW_LENGTH)
    _draw_arrowhead(ax, ex2, ey2, ex2 - ux * ARROW_LENGTH, ey2 - uy * ARROW_LENGTH)
    
    # Determine if vertical dimension (for text rotation per ISO 129)
    is_vertical = abs(ey2 - ey1) > abs(ex2 - ex1)
    
    # Text position - use TEXT_GAP_FROM_DIM_LINE for consistent spacing
    tx = (ex1 + ex2) / 2
    ty = (ey1 + ey2) / 2
    
    if is_vertical:
        # Vertical dimension: text rotated 90° counter-clockwise, positioned left of dimension line
        tx = min(ex1, ex2) - TEXT_GAP_FROM_DIM_LINE
        ax.text(tx, ty, text, color=C_TEXT, ha="right", va="center", rotation=90, **_dim_text_kwargs())
    else:
        # Horizontal dimension: text above dimension line
        ty += TEXT_GAP_FROM_DIM_LINE
        ax.text(tx, ty, text, color=C_TEXT, ha="center", va="bottom", **_dim_text_kwargs())


def draw_ext_outside(ax, px1, py1, px2, py2, dx, dy, text):
    """Draw external dimension (arrows outside extension lines)."""
    text = _format_dim_text(text)
    ex1, ey1 = px1 + dx, py1 + dy
    ex2, ey2 = px2 + dx, py2 + dy
    
    if not ISO_PDF_ACTIVE:
        # Original web style - uses matplotlib annotate
        sgx = np.sign(dx) if dx != 0 else 0
        sgy = np.sign(dy) if dy != 0 else 0
        ax.plot([px1, ex1 + sgx * 0.5], [py1, ey1 + sgy * 0.5], "k-", lw=DIM_LINE_WIDTH)
        ax.plot([px2, ex2 + sgx * 0.5], [py2, ey2 + sgy * 0.5], "k-", lw=DIM_LINE_WIDTH)
        vec_x, vec_y = ex2 - ex1, ey2 - ey1
        dist = np.sqrt(vec_x**2 + vec_y**2)
        if dist == 0:
            return
        ux, uy = vec_x / dist, vec_y / dist
        ax.annotate(
            "",
            xy=(ex1, ey1),
            xytext=(ex1 - ux * 3, ey1 - uy * 3),
            arrowprops=dict(arrowstyle="-|>,head_length=1,head_width=0.175", color="black", lw=DIM_LINE_WIDTH, mutation_scale=10.0),
        )
        ax.annotate(
            "",
            xy=(ex2, ey2),
            xytext=(ex2 + ux * 3, ey2 + uy * 3),
            arrowprops=dict(arrowstyle="-|>,head_length=1,head_width=0.175", color="black", lw=DIM_LINE_WIDTH, mutation_scale=10.0),
        )
        ax.text(
            ex2 + ux * 5,
            ey2 + uy * 5,
            text,
            color=C_TEXT,
            ha="center",
            va="center",
            bbox=dict(facecolor="#ffffff", edgecolor="none", pad=1),
            fontsize=9,
        )
        return

    # ISO PDF style - arrows touch extension lines exactly
    # Draw extension lines
    s1x, s1y, e1x, e1y = _extension_segment(px1, py1, ex1, ey1)
    s2x, s2y, e2x, e2y = _extension_segment(px2, py2, ex2, ey2)
    ax.plot([s1x, e1x], [s1y, e1y], "k-", lw=EXT_LINE_WIDTH, solid_capstyle="butt")
    ax.plot([s2x, e2x], [s2y, e2y], "k-", lw=EXT_LINE_WIDTH, solid_capstyle="butt")
    
    # Compute direction vector
    vec_x, vec_y = ex2 - ex1, ey2 - ey1
    dist = np.hypot(vec_x, vec_y)
    if dist <= 1e-12:
        return
    ux, uy = vec_x / dist, vec_y / dist
    
    # Extension beyond arrow tips (tail length)
    # Right tail is longer to support text
    line_extra_left = 2.0
    line_extra_right = OUTSIDE_TEXT_DIST
    
    # Draw dimension line (extends beyond arrow tips)
    ax.plot([ex1 - ux * line_extra_left, ex2 + ux * line_extra_right], 
            [ey1 - uy * line_extra_left, ey2 + uy * line_extra_right], "k-", lw=DIM_LINE_WIDTH, solid_capstyle="butt")
    
    # Draw arrowheads with tips at extension line positions (pointing outward)
    _draw_arrowhead(ax, ex1, ey1, ex1 - ux * ARROW_LENGTH, ey1 - uy * ARROW_LENGTH)
    _draw_arrowhead(ax, ex2, ey2, ex2 + ux * ARROW_LENGTH, ey2 + uy * ARROW_LENGTH)
    
    # Position text
    if abs(ex2 - ex1) >= abs(ey2 - ey1):
        # Horizontal dimension
        tx = max(ex1, ex2) + OUTSIDE_TEXT_DIST * OUTSIDE_TEXT_OFFSET_RATIO
        ty = max(ey1, ey2) + TEXT_GAP_FROM_DIM_LINE
        ax.text(tx, ty, text, color=C_TEXT, ha="center", va="bottom", **_dim_text_kwargs())
    else:
        # Vertical dimension: text rotated 90° counter-clockwise
        tx = min(ex1, ex2) - TEXT_GAP_FROM_DIM_LINE
        ty = (ey1 + ey2) / 2
        ax.text(tx, ty, text, color=C_TEXT, ha="right", va="center", rotation=90, **_dim_text_kwargs())


def draw_pointer(ax, p_target, p_text, text):
    """Draw radius/pointer dimension. Arrow tip touches the profile."""
    text = _format_dim_text(text)
    tx, ty = p_text
    px, py = p_target
    
    if not ISO_PDF_ACTIVE:
        # Original web style - uses matplotlib annotate
        ax.annotate(
            text,
            xy=p_target,
            xytext=p_text,
            arrowprops=dict(arrowstyle="-|>,head_length=1,head_width=0.175", color="black", lw=DIM_LINE_WIDTH, mutation_scale=10.0),
            color=C_TEXT,
            ha="center",
            va="center",
            bbox=dict(facecolor="#ffffff", edgecolor="none", pad=0.5),
            fontsize=9,
        )
        return

    # ISO PDF style - arrow touches profile exactly
    # Direction from text to target
    vec_x = px - tx
    vec_y = py - ty
    dist = np.hypot(vec_x, vec_y)
    if dist <= 1e-12:
        return
    ux, uy = vec_x / dist, vec_y / dist

    # Draw leader line (stops before arrow)
    ax.plot([tx, px - ux * ARROW_LENGTH], [ty, py - uy * ARROW_LENGTH], "k-", lw=DIM_LINE_WIDTH)
    
    # Draw arrowhead with tip at target (touching profile)
    _draw_arrowhead(ax, px, py, px - ux * ARROW_LENGTH, py - uy * ARROW_LENGTH)
    
    # Draw text shelf and text
    side = 1.0 if tx >= px else -1.0
    shelf_end_x = tx + side * 3.25
    ax.plot([tx, shelf_end_x], [ty, ty], "k-", lw=DIM_LINE_WIDTH)
    ax.text((tx + shelf_end_x) / 2, ty + TEXT_GAP_FROM_DIM_LINE, text, color=C_TEXT, ha="center", va="bottom", **_dim_text_kwargs())


def get_circle_contour(radius, density=300):
    t = np.linspace(0, 2 * np.pi, density)
    return radius * np.cos(t), radius * np.sin(t)


def get_capsule_contour(l_val, w_val, density=160):
    r = w_val / 2
    l_flat = max(0, l_val - w_val)
    t_top = np.linspace(0, np.pi, density)
    t_bot = np.linspace(np.pi, 2 * np.pi, density)
    x_top, y_top = l_flat / 2 + r * np.sin(t_top), r * np.cos(t_top)
    x_bot, y_bot = -l_flat / 2 + r * np.sin(t_bot), r * np.cos(t_bot)
    return np.concatenate([x_top, x_bot, [x_top[0]]]), np.concatenate([y_top, y_bot, [y_top[0]]])


def get_oval_contour(l_val, w_val, re, rs, density=120):
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


def _shape_meta(cfg):
    shape = cfg.shape
    is_modified = bool(cfg.is_modified)
    w_val = max(0.1, cfg.W)
    l_val = max(0.1, cfg.L)
    if shape == "round":
        l_val = w_val
    if l_val < w_val:
        l_val = w_val
    land = max(0.0, cfg.Land)
    re = min(max(0.01, cfg.Re), w_val / 2 - 0.01)
    rs = max(l_val / 2 + 0.01, cfg.Rs)
    return shape, is_modified, w_val, l_val, land, re, rs


def _major_profile_x(x_1d, params, cfg, shape, is_modified, l_val, w_val, land, dc):
    if shape == "round":
        span = max(0.001, w_val / 2 - land)
        return get_1d_z_engine(np.abs(x_1d), params, span, dc)
    if shape == "capsule":
        l_flat = max(0, l_val - w_val)
        span = max(0.001, w_val / 2 - land)
        rho = np.maximum(0, np.abs(x_1d) - l_flat / 2)
        return get_1d_z_engine(rho, params, span, dc)
    span = max(0.001, l_val / 2 - land)
    if shape == "oval" and cfg.profile == "concave":
        # For oval concave, major side view must use major cup radius from source logic.
        params_major = dict(params)
        params_major["Rc_min"] = cfg.Rc_maj
        return get_1d_z_engine(np.abs(x_1d), params_major, span, dc)
    return get_1d_z_engine(np.abs(x_1d), params, span, dc)


def _minor_profile_y(y_1d, params, cfg, w_val, land, dc):
    span = max(0.001, w_val / 2 - land)
    if cfg.shape == "oval" and cfg.profile == "compound":
        return get_compound_profile(
            np.abs(y_1d),
            cfg.R_min_maj,
            cfg.R_min_min,
            dc,
            span,
        )
    return get_1d_z_engine(np.abs(y_1d), params, span, dc)


def apply_1d_groove(x_1d, z_surf, cfg, edge_rad):
    b_type = cfg.b_type
    b_depth = cfg.b_depth
    b_angle = cfg.b_angle
    b_ri = cfg.b_Ri
    dc = cfg.Dc

    if b_type == "none" or b_depth <= 0:
        return z_surf
    alpha = np.radians(b_angle / 2.0)
    if alpha <= 0:
        return z_surf
    d_sharp = b_ri / np.sin(alpha) - b_ri if b_ri > 0 else 0
    x_ti = b_ri * np.sin(alpha)
    x_abs = np.abs(x_1d)
    center_idx = np.argmin(x_abs)
    z_center = z_surf[center_idx]

    if b_type == "standard":
        z_b = z_center - b_depth
    elif b_type == "cut_through":
        z_b = dc - b_depth
    elif b_type == "decreasing":
        z_b = z_center - b_depth * np.maximum(0, 1 - (x_abs / max(1e-6, edge_rad)) ** 2)
    else:
        z_b = z_center - b_depth

    z_v = z_b - d_sharp + x_abs / np.tan(alpha)
    z_inner = z_b + b_ri - np.sqrt(np.maximum(0, b_ri**2 - x_abs**2))
    z_g = np.where(x_abs <= x_ti, z_inner, z_v)
    return np.minimum(z_surf, z_g)


def render_tablet(mesh_data, params, dpi=120, output_format=None):
    global DIM_LINE_WIDTH, C_TEXT
    global EXT_LINE_WIDTH, TEXT_FONT_SIZE, TEXT_GAP_FROM_DIM_LINE
    global TEXT_BBOX_PAD, EXT_LINE_GAP_FROM_FEATURE, EXT_LINE_OVERRUN, OUTSIDE_TEXT_DIST
    global OUTSIDE_TEXT_OFFSET_RATIO, ARROW_LENGTH, ARROW_WIDTH, ISO_PDF_ACTIVE
    
    style_name = str(params.get("render_2d_style", "web")).lower()
    ISO_PDF_ACTIVE = style_name == "iso_pdf"
    
    if ISO_PDF_ACTIVE:
        style = ISO_PDF_STYLE
        DIM_LINE_WIDTH = style["dim_line_width"]
        EXT_LINE_WIDTH = style["ext_line_width"]
        C_TEXT = style["text_color"]
        pdf_scale_ratio = float(params.get("render_2d_pdf_scale_ratio", 1.0) or 1.0)
        if pdf_scale_ratio <= 0:
            pdf_scale_ratio = 1.0
        # Keep text size visually fixed in PDF even when geometry is scaled in placement.
        # User-requested boost: 4x larger labels in PDF 2D drawing.
        TEXT_FONT_SIZE = (style["text_font_size"] * 4.0) / pdf_scale_ratio
        TEXT_GAP_FROM_DIM_LINE = style["text_gap_from_dim_line"]
        TEXT_BBOX_PAD = style["text_bbox_pad"]
        EXT_LINE_GAP_FROM_FEATURE = style["ext_line_gap_from_feature"]
        EXT_LINE_OVERRUN = style["ext_line_overrun"]
        OUTSIDE_TEXT_DIST = style["outside_text_dist"]
        OUTSIDE_TEXT_OFFSET_RATIO = style["outside_text_offset_ratio"]
        ARROW_LENGTH = style["arrow_length"]
        ARROW_WIDTH = style["arrow_width"]
        poly_fill_color = params.get("pdf_2d_fill_color", "#dec9bd")
    else:
        style = WEB_STYLE
        DIM_LINE_WIDTH = style["dim_line_width"]
        C_TEXT = params.get("web_2d_dim_color", style["text_color"])
        poly_fill_color = params.get("web_2d_fill_color", "#dec9bd")

    base_fill_rgb = to_rgb(poly_fill_color)

    cfg = _validate_params(params)
    shape, is_modified, w_val, l_val, land, re, rs = _shape_meta(cfg)
    hb = cfg.Hb
    dc = cfg.Dc
    tt = cfg.Tt
    profile = cfg.profile
    
    if ISO_PDF_ACTIVE:
        render_2d_shaded = bool(params.get("pdf_2d_shaded", True))
    else:
        render_2d_shaded = bool(params.get("render_2d_shaded", False))
        
    b_type = cfg.b_type
    b_depth = cfg.b_depth
    b_double_sided = bool(cfg.b_double_sided)
    b_cruciform = bool(cfg.b_cruciform)
    b_angle = cfg.b_angle
    b_ri = cfg.b_Ri
    bev_a = cfg.Bev_A
    r_edge = cfg.R_edge
    x_grid, y_grid = mesh_data["x_grid"], mesh_data["y_grid"]

    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor("#ffffff")
    ax.set_aspect("equal")
    ax.axis("off")

    cx_top, cy_top = 0, 0
    cx_side, cy_side = -(w_val / 2 + tt / 2 + 15), 0
    cx_front, cy_front = 0, -(l_val / 2 + tt / 2 + 15)
    l_flat = max(0.0, l_val - w_val)
    oval_ref_flat_side = None
    oval_ref_flat_front = None

    if shape == "round":
        x_out, y_out = get_circle_contour(w_val / 2)
        if render_2d_shaded:
            _draw_shaded_polygon(ax, x_out + cx_top, y_out + cy_top, base_rgb=base_fill_rgb, alpha=0.95)
        ax.plot(x_out + cx_top, y_out + cy_top, "k-", linewidth=1.2)
        r_c = max(0.01, w_val / 2 - land)
        if land > 0:
            x_in, y_in = get_circle_contour(r_c)
            ax.plot(x_in + cx_top, y_in + cy_top, "k-", linewidth=0.6)
        if profile == "ffre":
            r_edge = cfg.R_edge
            dx_curve = np.sqrt(max(0.0, r_edge**2 - (r_edge - dc) ** 2))
            flat_rad = max(0.0, r_c - dx_curve)
            if flat_rad > 0.05:
                x_flat, y_flat = get_circle_contour(flat_rad)
                if render_2d_shaded:
                    _draw_solid_polygon(ax, x_flat + cx_top, y_flat + cy_top, color=poly_fill_color, alpha=0.97, zorder=0.36)
                ax.plot(x_flat + cx_top, y_flat + cy_top, "k--", linewidth=0.6)
        elif profile == "ffbe":
            r_blend = max(0.0, min(cfg.Blend_R, dc))
            alpha_rad = np.radians(cfg.Bev_A)
            if 1e-6 < alpha_rad < (np.pi / 2 - 1e-6):
                tan_a = np.tan(alpha_rad)
                sin_a = np.sin(alpha_rad)
                if abs(tan_a) > 1e-9 and abs(sin_a) > 1e-9:
                    d_inset = (dc - r_blend) / tan_a + r_blend / sin_a
                    flat_rad = max(0.0, r_c - d_inset)
                    if flat_rad > 0.05:
                        x_flat, y_flat = get_circle_contour(flat_rad)
                        if render_2d_shaded:
                            _draw_solid_polygon(ax, x_flat + cx_top, y_flat + cy_top, color=poly_fill_color, alpha=0.97, zorder=0.36)
                        ax.plot(x_flat + cx_top, y_flat + cy_top, "k--", linewidth=0.6)
        draw_ext(ax, cx_top - w_val / 2, cy_top + w_val / 2, cx_top - w_val / 2, cy_top - w_val / 2, -4.5, 0, f"{w_val:g}\nDiameter")
    elif shape == "capsule" and not is_modified:
        x_out, y_out = get_capsule_contour(l_val, w_val)
        if render_2d_shaded:
            _draw_shaded_polygon(ax, y_out + cx_top, x_out + cy_top, base_rgb=base_fill_rgb, alpha=0.95)
        ax.plot(y_out + cx_top, x_out + cy_top, "k-", linewidth=1.2)
        if land > 0:
            x_in, y_in = get_capsule_contour(max(0.1, l_val - 2 * land), max(0.1, w_val - 2 * land))
            ax.plot(y_in + cx_top, x_in + cy_top, "k-", linewidth=0.6)
        if profile == "ffre":
            r_c = max(0.01, w_val / 2 - land)
            r_edge = max(0.0, cfg.R_edge)
            dx_curve = np.sqrt(max(0.0, r_edge**2 - (r_edge - dc) ** 2))
            r_flat = max(0.0, r_c - dx_curve)
            if r_flat > 0.05:
                flat_l = l_flat + 2 * r_flat
                flat_w = 2 * r_flat
                x_flat, y_flat = get_capsule_contour(flat_l, flat_w)
                if render_2d_shaded:
                    _draw_solid_polygon(ax, y_flat + cx_top, x_flat + cy_top, color=poly_fill_color, alpha=0.97, zorder=0.36)
                ax.plot(y_flat + cx_top, x_flat + cy_top, "k--", linewidth=0.6)
        elif profile == "ffbe":
            r_c = max(0.01, w_val / 2 - land)
            r_blend = max(0.0, min(cfg.Blend_R, dc))
            alpha_rad = np.radians(cfg.Bev_A)
            if 1e-6 < alpha_rad < (np.pi / 2 - 1e-6):
                tan_a = np.tan(alpha_rad)
                sin_a = np.sin(alpha_rad)
                if abs(tan_a) > 1e-9 and abs(sin_a) > 1e-9:
                    d_inset = (dc - r_blend) / tan_a + r_blend / sin_a
                    r_flat = max(0.0, r_c - d_inset)
                    if r_flat > 0.05:
                        flat_l = l_flat + 2 * r_flat
                        flat_w = 2 * r_flat
                        x_flat, y_flat = get_capsule_contour(flat_l, flat_w)
                        if render_2d_shaded:
                            _draw_solid_polygon(ax, y_flat + cx_top, x_flat + cy_top, color=poly_fill_color, alpha=0.97, zorder=0.36)
                        ax.plot(y_flat + cx_top, x_flat + cy_top, "k--", linewidth=0.6)
        draw_ext(ax, cx_top - w_val / 2, cy_top + l_val / 2, cx_top + w_val / 2, cy_top + l_val / 2, 0, 4, f"{w_val:g}\nMinor Axis")
        draw_ext(ax, cx_top - w_val / 2, cy_top - l_val / 2, cx_top - w_val / 2, cy_top + l_val / 2, -4.5, 0, f"{l_val:g}\nMajor Axis")
    else:
        x_out, y_out = get_oval_contour(l_val, w_val, re, rs)
        if render_2d_shaded:
            _draw_shaded_polygon(ax, y_out + cx_top, x_out + cy_top, base_rgb=base_fill_rgb, alpha=0.95)
        ax.plot(y_out + cx_top, x_out + cy_top, "k-", linewidth=1.2)
        if land > 0 and re > land and rs > land:
            x_in, y_in = get_oval_contour(l_val - 2 * land, w_val - 2 * land, re - land, rs - land)
            ax.plot(y_in + cx_top, x_in + cy_top, "k-", linewidth=0.6)
        l_c_oval = max(0.001, l_val / 2 - land)
        w_c_oval = max(0.001, w_val / 2 - land)
        if profile == "ffre":
            r_edge_oval = max(0.0, cfg.R_edge)
            dx_curve = np.sqrt(max(0.0, r_edge_oval**2 - (r_edge_oval - dc) ** 2))
            l_flat_half = max(0.0, l_c_oval - dx_curve)
            w_flat_half = max(0.0, w_c_oval - dx_curve)
            if l_flat_half > 0.05 and w_flat_half > 0.05:
                l_flat_dim = l_val - 2 * land - 2 * dx_curve
                w_flat_dim = w_val - 2 * land - 2 * dx_curve
                re_flat = re - land - dx_curve
                rs_flat = rs - land - dx_curve
                if re_flat > 0.01 and rs_flat > 0.01 and w_flat_dim > 0.1 and l_flat_dim > 0.1:
                    x_flat_cont, y_flat_cont = get_oval_contour(l_flat_dim, w_flat_dim, re_flat, rs_flat)
                    if render_2d_shaded:
                        _draw_solid_polygon(ax, y_flat_cont + cx_top, x_flat_cont + cy_top, color=poly_fill_color, alpha=0.97, zorder=0.36)
                    # Source uses solid contour for this line.
                    ax.plot(y_flat_cont + cx_top, x_flat_cont + cy_top, "k-", linewidth=0.6)
                    oval_ref_flat_side = 2 * l_flat_half
                    oval_ref_flat_front = 2 * w_flat_half
        elif profile == "ffbe":
            r_blend_oval = max(0.0, min(cfg.Blend_R, dc))
            alpha_oval = np.radians(cfg.Bev_A)
            if 1e-6 < alpha_oval < (np.pi / 2 - 1e-6):
                tan_oval = np.tan(alpha_oval)
                sin_oval = np.sin(alpha_oval)
                if abs(tan_oval) > 1e-9 and abs(sin_oval) > 1e-9:
                    d_inset = (dc - r_blend_oval) / tan_oval + r_blend_oval / sin_oval
                    l_flat_half = max(0.0, l_c_oval - d_inset)
                    w_flat_half = max(0.0, w_c_oval - d_inset)
                    if l_flat_half > 0.05 and w_flat_half > 0.05:
                        l_flat_dim = l_val - 2 * land - 2 * d_inset
                        w_flat_dim = w_val - 2 * land - 2 * d_inset
                        re_flat = re - land - d_inset
                        rs_flat = rs - land - d_inset
                        if re_flat > 0.01 and rs_flat > 0.01 and w_flat_dim > 0.1 and l_flat_dim > 0.1:
                            x_flat_cont, y_flat_cont = get_oval_contour(l_flat_dim, w_flat_dim, re_flat, rs_flat)
                            if render_2d_shaded:
                                _draw_solid_polygon(ax, y_flat_cont + cx_top, x_flat_cont + cy_top, color=poly_fill_color, alpha=0.97, zorder=0.36)
                            # Source uses solid contour for this line.
                            ax.plot(y_flat_cont + cx_top, x_flat_cont + cy_top, "k-", linewidth=0.6)
                            oval_ref_flat_side = 2 * l_flat_half
                            oval_ref_flat_front = 2 * w_flat_half
        draw_ext(ax, cx_top - w_val / 2, cy_top + l_val / 2, cx_top + w_val / 2, cy_top + l_val / 2, 0, 4, f"{w_val:g}\nMinor Axis")
        draw_ext(ax, cx_top - w_val / 2, cy_top - l_val / 2, cx_top - w_val / 2, cy_top + l_val / 2, -4.5, 0, f"{l_val:g}\nMajor Axis")
        draw_pointer(ax, (cx_top + w_val / 2, cy_top), (cx_top + w_val / 2 + 4, cy_top - l_val / 4), f"{rs:g}\nSide Radius")
        pt_x = re * np.sin(np.pi / 4)
        pt_y = -(l_val / 2 - re) - re * np.cos(np.pi / 4)
        draw_pointer(ax, (cx_top + pt_x, cy_top + pt_y), (cx_top + pt_x + 4, cy_top + pt_y - 4), f"{re:g}\nEnd Radius")

    if b_type != "none" and b_depth > 0:
        z, z_groove, mask_cup = mesh_data["Z"], mesh_data["Z_groove"], mesh_data["mask_cup"]
        if render_2d_shaded:
            groove_mask = np.where(mask_cup & ((z - z_groove) > 1e-6), 1.0, np.nan)
            if np.any(np.isfinite(groove_mask)):
                if shape == "round":
                    ax.contourf(
                        mesh_data["X"] + cx_top,
                        mesh_data["Y"] + cy_top,
                        groove_mask,
                        levels=[0.5, 1.5],
                        colors=[poly_fill_color],
                        antialiased=True,
                        zorder=0.33,
                    )
                else:
                    ax.contourf(
                        mesh_data["Y"] + cx_top,
                        mesh_data["X"] + cy_top,
                        groove_mask,
                        levels=[0.5, 1.5],
                        colors=[poly_fill_color],
                        antialiased=True,
                        zorder=0.33,
                    )
        z_diff_masked = np.where(mask_cup, z - z_groove, np.nan)
        z_groove_masked = np.where(mask_cup, z_groove, np.nan)
        if shape == "round":
            ax.contour(mesh_data["X"] + cx_top, mesh_data["Y"] + cy_top, z_diff_masked, levels=[0], colors="k", linewidths=0.8)
            ax.contour(mesh_data["X"] + cx_top, mesh_data["Y"] + cy_top, z_groove_masked, levels=[0], colors="k", linewidths=0.6)
        else:
            ax.contour(mesh_data["Y"] + cx_top, mesh_data["X"] + cy_top, z_diff_masked, levels=[0], colors="k", linewidths=0.8)
            ax.contour(mesh_data["Y"] + cx_top, mesh_data["X"] + cy_top, z_groove_masked, levels=[0], colors="k", linewidths=0.6)

        x_ti = b_ri * np.sin(np.radians(b_angle / 2.0))
        if x_ti > 0.005:
            if shape == "round":
                vis = z - z_groove
                if b_type == "standard":
                    # For Standard, use Natoli clipping by groove floor at ends.
                    vis = np.minimum(vis, z_groove)
                vis_mask = np.where(mask_cup, vis >= 0, False)

                ti_field_y = np.where(vis_mask, np.abs(mesh_data["Y"]) - x_ti, np.nan)
                ax.contour(mesh_data["X"] + cx_top, mesh_data["Y"] + cy_top, ti_field_y, levels=[0], colors="k", linewidths=0.6)
                if b_cruciform:
                    ti_field_x = np.where(vis_mask, np.abs(mesh_data["X"]) - x_ti, np.nan)
                    ax.contour(mesh_data["X"] + cx_top, mesh_data["Y"] + cy_top, ti_field_x, levels=[0], colors="k", linewidths=0.6)
            else:
                idx_x = np.argmin(np.abs(x_grid - x_ti))
                cond = (z - z_groove)[:, idx_x]
                if b_type == "standard":
                    cond = np.minimum(cond, z_groove[:, idx_x])
                cond = np.where(mask_cup[:, idx_x], cond, -1.0)
                valid_indices = np.where(cond >= 0)[0]
                if len(valid_indices) > 0:
                    i_min, i_max = valid_indices[0], valid_indices[-1]
                    y_start, y_end = y_grid[i_min], y_grid[i_max]
                    if i_min > 0:
                        c0, c1 = cond[i_min], cond[i_min - 1]
                        if c0 != c1:
                            y_start = y_grid[i_min] - c0 * (y_grid[i_min - 1] - y_grid[i_min]) / (c1 - c0)
                    if i_max < len(y_grid) - 1:
                        c0, c1 = cond[i_max], cond[i_max + 1]
                        if c0 != c1:
                            y_end = y_grid[i_max] - c0 * (y_grid[i_max + 1] - y_grid[i_max]) / (c1 - c0)
                    ax.plot([y_start + cx_top, y_end + cx_top], [x_ti + cy_top, x_ti + cy_top], "k-", lw=0.6)
                    ax.plot([y_start + cx_top, y_end + cx_top], [-x_ti + cy_top, -x_ti + cy_top], "k-", lw=0.6)

    capsule_r_flat = None

    if shape == "round":
        span = max(0.001, w_val / 2 - land)
        l_side = w_val
    else:
        span = max(0.001, l_val / 2 - land)
        l_side = l_val
    x_maj = np.linspace(-span, span, 400)
    z_up_maj_base = _major_profile_x(x_maj, params, cfg, shape, is_modified, l_val, w_val, land, dc)
    z_up_maj = apply_1d_groove(x_maj, z_up_maj_base, cfg, max(0.001, span))
    z_down_maj = apply_1d_groove(x_maj, z_up_maj_base, cfg, max(0.001, span)) if b_double_sided else z_up_maj_base

    l_prof = np.concatenate(
        [
            [-l_side / 2, -l_side / 2],
            [-l_side / 2, -span],
            x_maj,
            [span, l_side / 2],
            [l_side / 2, l_side / 2],
            [l_side / 2, span],
            x_maj[::-1],
            [-span, -l_side / 2],
            [-l_side / 2],
        ]
    )
    t_prof = np.concatenate(
        [
            [-hb / 2, hb / 2],
            [hb / 2, hb / 2],
            z_up_maj + hb / 2,
            [hb / 2, hb / 2],
            [hb / 2, -hb / 2],
            [-hb / 2, -hb / 2],
            -(z_down_maj + hb / 2)[::-1],
            [-hb / 2, -hb / 2],
            [-hb / 2],
        ]
    )
    if render_2d_shaded:
        _draw_shaded_polygon(
            ax,
            t_prof + cx_side,
            l_prof + cy_side,
            base_rgb=base_fill_rgb,
            alpha=0.95,
            rotate_90=True,
        )
    ax.plot(t_prof + cx_side, l_prof + cy_side, "k-", linewidth=1.2)
    ax.plot([-hb / 2 + cx_side, -hb / 2 + cx_side], [-l_side / 2 + cy_side, l_side / 2 + cy_side], "k-", linewidth=1.2)
    ax.plot([hb / 2 + cx_side, hb / 2 + cx_side], [-l_side / 2 + cy_side, l_side / 2 + cy_side], "k-", linewidth=1.2)
    draw_ext_outside(ax, cx_side + hb / 2, cy_side + l_side / 2, cx_side + hb / 2 + dc, cy_side + l_side / 2, 0, 4, f"{dc:g}\nCup Depth")
    if profile == "cbe":
        bev_d = cfg.Bev_D
        if bev_d > 0:
            draw_ext_outside(ax, cx_side + hb / 2, cy_side + l_side / 2, cx_side + hb / 2 + bev_d, cy_side + l_side / 2, 0, 2, f"{bev_d:g}\nBevel Depth")
    draw_ext_outside(ax, cx_side - hb / 2, cy_side - l_side / 2, cx_side + hb / 2, cy_side - l_side / 2, 0, -4, f"{hb:g}\nBelly Band")
    if shape == "capsule" and l_flat > 0:
        ref_flat_side = l_flat
        if profile == "ffre":
            r_c_caps = max(0.01, w_val / 2 - land)
            r_edge_caps = max(0.0, cfg.R_edge)
            dx_curve = np.sqrt(max(0.0, r_edge_caps**2 - (r_edge_caps - dc) ** 2))
            capsule_r_flat = max(0.0, r_c_caps - dx_curve)
            ref_flat_side = l_flat + 2 * capsule_r_flat
        elif profile == "ffbe":
            r_c_caps = max(0.01, w_val / 2 - land)
            r_blend_caps = max(0.0, min(cfg.Blend_R, dc))
            alpha_caps = np.radians(cfg.Bev_A)
            if 1e-6 < alpha_caps < (np.pi / 2 - 1e-6):
                tan_caps = np.tan(alpha_caps)
                sin_caps = np.sin(alpha_caps)
                if abs(tan_caps) > 1e-9 and abs(sin_caps) > 1e-9:
                    d_inset_caps = (dc - r_blend_caps) / tan_caps + r_blend_caps / sin_caps
                    capsule_r_flat = max(0.0, r_c_caps - d_inset_caps)
                    ref_flat_side = l_flat + 2 * capsule_r_flat
        draw_ext(ax, cx_side + hb / 2 + dc, cy_side + ref_flat_side / 2, cx_side + hb / 2 + dc, cy_side - ref_flat_side / 2, 4.5, 0, f"{ref_flat_side:g}\nRef. Flat")
    if shape == "oval" and profile in ("ffre", "ffbe") and oval_ref_flat_side is not None and oval_ref_flat_side > 0:
        draw_ext(
            ax,
            cx_side + hb / 2 + dc,
            cy_side + oval_ref_flat_side / 2,
            cx_side + hb / 2 + dc,
            cy_side - oval_ref_flat_side / 2,
            4.5,
            0,
            f"{oval_ref_flat_side:.3f}\nRef. Flat",
        )

    if shape == "oval" and profile not in ("compound", "modified_oval", "ffbe", "ffre"):
        rc_maj = cfg.Rc_maj
        p_idx = np.argmin(np.abs(x_maj - (-l_side / 4)))
        pt_surf = z_up_maj[p_idx] + hb / 2
        pt_len = x_maj[p_idx]
        draw_pointer(ax, (pt_surf + cx_side, pt_len + cy_side), (pt_surf + cx_side + 4, pt_len + cy_side - l_side / 4), f"{rc_maj:g}\nCup Radius\nMajor")
    elif shape == "oval" and profile in ("modified_oval", "compound"):
        r_maj_maj = cfg.R_maj_maj
        r_maj_min = cfg.R_maj_min
        l_c = max(0.001, l_val / 2 - land)
        # Use shorter leader for PDF, longer for web
        leader_offset = 4 if ISO_PDF_ACTIVE else 7
        x_maj_pt = l_c * 0.30
        z_maj_pt = get_compound_profile(np.array([x_maj_pt]), r_maj_maj, r_maj_min, dc, l_c)[0]
        target_maj = (cx_side + hb / 2 + z_maj_pt, cy_side + x_maj_pt)
        text_maj = (cx_side + hb / 2 + z_maj_pt + leader_offset, cy_side + x_maj_pt + 2)
        draw_pointer(ax, target_maj, text_maj, f"{r_maj_maj:g}\nMajor Major\nRadius")

        x_min_pt = l_c * 0.85
        z_min_pt = get_compound_profile(np.array([x_min_pt]), r_maj_maj, r_maj_min, dc, l_c)[0]
        target_min = (cx_side + hb / 2 + z_min_pt, cy_side - x_min_pt)
        text_min = (cx_side + hb / 2 + z_min_pt + leader_offset, cy_side - x_min_pt + 2.5)
        draw_pointer(ax, target_min, text_min, f"{r_maj_min:g}\nMajor Minor\nRadius")

    span_front = max(0.001, w_val / 2 - land)
    y_min_cup = np.linspace(-span_front, span_front, 400)
    z_up_min = _minor_profile_y(y_min_cup, params, cfg, w_val, land, dc)
    w_prof = np.concatenate(
        [
            [-w_val / 2, -w_val / 2],
            [-w_val / 2, -span_front],
            y_min_cup,
            [span_front, w_val / 2],
            [w_val / 2, w_val / 2],
            [w_val / 2, span_front],
            y_min_cup[::-1],
            [-span_front, -w_val / 2],
            [-w_val / 2],
        ]
    )
    t_front = np.concatenate(
        [
            [-hb / 2, hb / 2],
            [hb / 2, hb / 2],
            z_up_min + hb / 2,
            [hb / 2, hb / 2],
            [hb / 2, -hb / 2],
            [-hb / 2, -hb / 2],
            -(z_up_min + hb / 2)[::-1],
            [-hb / 2, -hb / 2],
            [-hb / 2],
        ]
    )
    if render_2d_shaded:
        _draw_shaded_polygon(ax, w_prof + cx_front, t_front + cy_front, base_rgb=base_fill_rgb, alpha=0.95)
    ax.plot(w_prof + cx_front, t_front + cy_front, "k-", linewidth=1.2)
    ax.plot([-w_val / 2 + cx_front, w_val / 2 + cx_front], [hb / 2 + cy_front, hb / 2 + cy_front], "k-", linewidth=1.2)
    ax.plot([-w_val / 2 + cx_front, w_val / 2 + cx_front], [-hb / 2 + cy_front, -hb / 2 + cy_front], "k-", linewidth=1.2)
    draw_ext(ax, cx_front - w_val / 2, cy_front - tt / 2, cx_front - w_val / 2, cy_front + tt / 2, -4.5, 0, f"{tt:g}\nThickness")

    if b_type != "none" and b_depth > 0:
        if b_type == "standard":
            z_bottom_line = z_up_min - b_depth
        elif b_type == "cut_through":
            z_bottom_line = np.full_like(y_min_cup, dc - b_depth)
        elif b_type == "decreasing":
            z_bottom_line = z_up_min - b_depth * np.maximum(0, 1 - (np.abs(y_min_cup) / max(1e-6, span_front)) ** 2)
        else:
            z_bottom_line = z_up_min - b_depth
        valid = (z_bottom_line > 0) & (z_bottom_line < z_up_min)
        ax.plot(y_min_cup[valid] + cx_front, z_bottom_line[valid] + hb / 2 + cy_front, "k--", lw=0.8)
        if b_double_sided:
            ax.plot(y_min_cup[valid] + cx_front, -(z_bottom_line[valid] + hb / 2) + cy_front, "k--", lw=0.8)

    if land > 0:
        l_land_coord = span_front
        
        if not ISO_PDF_ACTIVE:
            # Original web style
            ax.plot([cx_front + l_land_coord, cx_front + l_land_coord], [cy_front + tt / 2, cy_front + tt / 2 + 2.5], "k-", lw=DIM_LINE_WIDTH)
            ax.plot([cx_front + w_val / 2, cx_front + w_val / 2], [cy_front + tt / 2, cy_front + tt / 2 + 2.5], "k-", lw=DIM_LINE_WIDTH)
            ax.annotate(
                "",
                xy=(cx_front + l_land_coord, cy_front + tt / 2 + 2),
                xytext=(cx_front + l_land_coord - 2.5, cy_front + tt / 2 + 2),
                arrowprops=dict(arrowstyle="-|>,head_length=1,head_width=0.175", color="black", lw=DIM_LINE_WIDTH, mutation_scale=10.0),
            )
            ax.annotate(
                "",
                xy=(cx_front + w_val / 2, cy_front + tt / 2 + 2),
                xytext=(cx_front + w_val / 2 + 2.5, cy_front + tt / 2 + 2),
                arrowprops=dict(arrowstyle="-|>,head_length=1,head_width=0.175", color="black", lw=DIM_LINE_WIDTH, mutation_scale=10.0),
            )
            ax.text(
                cx_front + w_val / 2 + 4.2,
                cy_front + tt / 2 + 2,
                f"{land:g}\nBld. Land",
                color=C_TEXT,
                ha="center",
                va="center",
                bbox=dict(facecolor="#ffffff", edgecolor="none", pad=0.5),
                fontsize=9,
            )
        else:
            # ISO PDF style - arrows touch extension lines with tails
            ax.plot([cx_front + l_land_coord, cx_front + l_land_coord], [cy_front + tt / 2, cy_front + tt / 2 + 2.5], "k-", lw=EXT_LINE_WIDTH)
            ax.plot([cx_front + w_val / 2, cx_front + w_val / 2], [cy_front + tt / 2, cy_front + tt / 2 + 2.5], "k-", lw=EXT_LINE_WIDTH)
            
            y_dim = cy_front + tt / 2 + 2
            x_left = cx_front + l_land_coord
            x_right = cx_front + w_val / 2
            
            # Tail lengths (right tail longer for text support)
            tail_left = 2.0
            tail_right = OUTSIDE_TEXT_DIST
            
            # Dimension line with tails
            ax.plot([x_left - tail_left, x_right + tail_right], [y_dim, y_dim], "k-", lw=DIM_LINE_WIDTH)
            
            # Arrows pointing outward
            _draw_arrowhead(ax, x_left, y_dim, x_left - ARROW_LENGTH, y_dim)
            _draw_arrowhead(ax, x_right, y_dim, x_right + ARROW_LENGTH, y_dim)
            
            ax.text(
                cx_front + w_val / 2 + OUTSIDE_TEXT_DIST * OUTSIDE_TEXT_OFFSET_RATIO,
                cy_front + tt / 2 + 2 + TEXT_GAP_FROM_DIM_LINE,
                _format_dim_text(f"{land:g}"),
                color=C_TEXT,
                ha="center",
                va="bottom",
                **_dim_text_kwargs(),
            )

    if profile in ("cbe", "ffbe"):
        alpha_rad = np.radians(bev_a)
        pt_x = cx_front + span_front
        pt_y = cy_front + hb / 2
        ext_len = w_val / 4.0
        # Horizontal guide to the right.
        ax.plot([pt_x, pt_x + ext_len], [pt_y, pt_y], "k-", lw=DIM_LINE_WIDTH)
        # Bevel guide down-right.
        dx = ext_len * np.cos(alpha_rad)
        dy = -ext_len * np.sin(alpha_rad)
        ax.plot([pt_x, pt_x + dx], [pt_y, pt_y + dy], "k-", lw=DIM_LINE_WIDTH)
        # Angle arc.
        arc_r = min(3.0, ext_len * 0.8)
        t_arc = np.linspace(-alpha_rad, 0, 20)
        ax.plot(pt_x + arc_r * np.cos(t_arc), pt_y + arc_r * np.sin(t_arc), "k-", lw=DIM_LINE_WIDTH)
        mid_ang = -alpha_rad / 2.0
        text_offset = 1.2
        ax.text(
            pt_x + (arc_r + text_offset) * np.cos(mid_ang),
            pt_y + (arc_r + text_offset) * np.sin(mid_ang),
            f"{bev_a:g}\N{DEGREE SIGN}",
            color=C_TEXT,
            ha="center",
            va="center",
            bbox=dict(facecolor="#ffffff", edgecolor="none", pad=TEXT_BBOX_PAD),
            **_dim_text_kwargs(),
        )

    if profile == "modified_oval" and shape == "oval":
        rc_min = cfg.Rc_min
        draw_pointer(ax, (cx_front, cy_front + tt / 2), (cx_front - w_val / 4, cy_front + tt / 2 + 4), f"{rc_min:g}\nCup Radius\nMinor")
    elif profile == "compound" and shape == "oval":
        r_min_maj = cfg.R_min_maj
        r_min_min = cfg.R_min_min
        x_min_maj_pt = span_front * 0.10
        z_min_maj_pt = get_compound_profile(np.array([x_min_maj_pt]), r_min_maj, r_min_min, dc, span_front)[0]
        targ_front_maj = (cx_front + x_min_maj_pt, cy_front + hb / 2 + z_min_maj_pt)
        txt_front_maj = (cx_front + x_min_maj_pt + 1.0, cy_front + hb / 2 + z_min_maj_pt + 4.5)
        draw_pointer(ax, targ_front_maj, txt_front_maj, f"{r_min_maj:g}\nMinor Major\nRadius")

        x_min_min_pt = span_front * 0.80
        z_min_min_pt = get_compound_profile(np.array([x_min_min_pt]), r_min_maj, r_min_min, dc, span_front)[0]
        targ_front_min = (cx_front - x_min_min_pt, cy_front + hb / 2 + z_min_min_pt)
        txt_front_min = (cx_front - x_min_min_pt - 2.5, cy_front + hb / 2 + z_min_min_pt + 4.5)
        draw_pointer(ax, targ_front_min, txt_front_min, f"{r_min_min:g}\nMinor Minor\nRadius")
    elif profile in ("compound",) and shape == "round":
        r_maj_maj = cfg.R_maj_maj
        r_maj_min = cfg.R_maj_min
        x_min_pt = span_front * 0.8
        z_min_pt = get_compound_profile(np.array([x_min_pt]), r_maj_maj, r_maj_min, dc, span_front)[0]
        draw_pointer(ax, (cx_front - x_min_pt, cy_front + hb / 2 + z_min_pt), (cx_front - x_min_pt - w_val / 6, cy_front + hb / 2 + z_min_pt + 5), f"{r_maj_min:g}\nMinor Radius")
        if shape == "round":
            x_maj_pt = span_front * 0.2
            z_maj_pt = get_compound_profile(np.array([x_maj_pt]), r_maj_maj, r_maj_min, dc, span_front)[0]
            draw_pointer(ax, (cx_front + x_maj_pt, cy_front + hb / 2 + z_maj_pt), (cx_front + x_maj_pt + 0.5, cy_front + hb / 2 + z_maj_pt + 5), f"{r_maj_maj:g}\nMajor Radius")
    elif profile == "ffbe":
        r_blend = max(0.0, min(cfg.Blend_R, dc))
        alpha_rad = np.radians(cfg.Bev_A)
        if r_blend > 0 and 1e-6 < alpha_rad < (np.pi / 2 - 1e-6):
            tan_a = np.tan(alpha_rad)
            sin_a = np.sin(alpha_rad)
            if abs(tan_a) > 1e-9 and abs(sin_a) > 1e-9:
                d_inset = (dc - r_blend) / tan_a + r_blend / sin_a
                if shape == "round":
                    round_r_flat = max(0.0, span_front - d_inset)
                    if round_r_flat > 0:
                        draw_ext_outside(
                            ax,
                            cx_front - round_r_flat,
                            cy_front - hb / 2 - dc,
                            cx_front + round_r_flat,
                            cy_front - hb / 2 - dc,
                            0,
                            -3,
                            f"{2 * round_r_flat:.3f}\nRef. Flat",
                        )
                w_target_val = -(span_front - d_inset + (r_blend * sin_a) / 2.0)
                z_min_pt = get_1d_z_engine(np.array([abs(w_target_val)]), params, span_front, dc)[0]
                draw_pointer(
                    ax,
                    (cx_front + w_target_val, cy_front + hb / 2 + z_min_pt),
                    (cx_front + w_target_val - w_val / 4.5, cy_front + hb / 2 + z_min_pt + 4),
                    f"{r_blend:g}\nBlend Radius",
                )
    elif profile == "ffre":
        r_c = span_front
        dx_curve = np.sqrt(max(0.0, r_edge**2 - (r_edge - dc) ** 2))
        if shape == "round":
            round_r_flat = max(0.0, r_c - dx_curve)
            if round_r_flat > 0:
                draw_ext_outside(
                    ax,
                    cx_front - round_r_flat,
                    cy_front - hb / 2 - dc,
                    cx_front + round_r_flat,
                    cy_front - hb / 2 - dc,
                    0,
                    -3,
                    f"{2 * round_r_flat:.3f}\nRef. Flat",
                )
        if shape == "capsule":
            capsule_r_flat = max(0.0, r_c - dx_curve)
            if capsule_r_flat > 0:
                draw_ext_outside(
                    ax,
                    cx_front - capsule_r_flat,
                    cy_front - hb / 2 - dc,
                    cx_front + capsule_r_flat,
                    cy_front - hb / 2 - dc,
                    0,
                    -3,
                    f"{2 * capsule_r_flat:.3f}\nRef. Flat",
                )
        w_target_val = -(r_c - dx_curve * 0.5)
        z_min_pt = get_1d_z_engine(np.array([abs(w_target_val)]), params, span_front, dc)[0]
        draw_pointer(
            ax,
            (cx_front + w_target_val, cy_front + hb / 2 + z_min_pt),
            (cx_front + w_target_val - w_val / 4.5, cy_front + hb / 2 + z_min_pt + 4),
            f"{r_edge:g}\nRadius",
        )
    if shape == "oval" and profile in ("ffre", "ffbe") and oval_ref_flat_front is not None and oval_ref_flat_front > 0:
        draw_ext_outside(
            ax,
            cx_front - oval_ref_flat_front / 2,
            cy_front - hb / 2 - dc,
            cx_front + oval_ref_flat_front / 2,
            cy_front - hb / 2 - dc,
            0,
            -3,
            f"{oval_ref_flat_front:.3f}\nRef. Flat",
        )
    if profile == "ffbe" and shape == "capsule":
        if capsule_r_flat is None:
            r_c_caps = span_front
            r_blend_caps = max(0.0, min(cfg.Blend_R, dc))
            alpha_caps = np.radians(cfg.Bev_A)
            if 1e-6 < alpha_caps < (np.pi / 2 - 1e-6):
                tan_caps = np.tan(alpha_caps)
                sin_caps = np.sin(alpha_caps)
                if abs(tan_caps) > 1e-9 and abs(sin_caps) > 1e-9:
                    d_inset_caps = (dc - r_blend_caps) / tan_caps + r_blend_caps / sin_caps
                    capsule_r_flat = max(0.0, r_c_caps - d_inset_caps)
        if capsule_r_flat and capsule_r_flat > 0:
            draw_ext_outside(
                ax,
                cx_front - capsule_r_flat,
                cy_front - hb / 2 - dc,
                cx_front + capsule_r_flat,
                cy_front - hb / 2 - dc,
                0,
                -3,
                f"{2 * capsule_r_flat:.3f}\nRef. Flat",
            )
    if profile in ("concave", "cbe"):
        rc_min = cfg.Rc_min
        draw_pointer(ax, (cx_front, cy_front + hb / 2 + dc), (cx_front - w_val / 4, cy_front + hb / 2 + dc + 4), f"{rc_min:g}\nCup Radius")

    def _compute_annotated_data_bounds():
        """Bounds in data units using geometry + dimension texts."""
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()

        if ax.dataLim is not None and np.isfinite(ax.dataLim.bounds).all():
            x0, y0, w0, h0 = ax.dataLim.bounds
            xmin, xmax = x0, x0 + w0
            ymin, ymax = y0, y0 + h0
        else:
            xmin = xmax = 0.0
            ymin = ymax = 0.0

        for txt in ax.texts:
            if not txt.get_visible():
                continue
            try:
                bbox = txt.get_window_extent(renderer=renderer)
            except Exception:
                continue
            if bbox is None:
                continue
            if not np.isfinite([bbox.x0, bbox.y0, bbox.x1, bbox.y1]).all():
                continue
            p0, p1 = ax.transData.inverted().transform(
                [[bbox.x0, bbox.y0], [bbox.x1, bbox.y1]]
            )
            xmin = min(xmin, p0[0], p1[0])
            xmax = max(xmax, p0[0], p1[0])
            ymin = min(ymin, p0[1], p1[1])
            ymax = max(ymax, p0[1], p1[1])

        return xmin, xmax, ymin, ymax

    x_min_val, x_max_val = cx_side - tt / 2 - 12, cx_top + w_val / 2 + 15
    y_min_val, y_max_val = cy_front - tt / 2 - 8, cy_top + l_val / 2 + 8
    center_x, center_y = (x_max_val + x_min_val) / 2, (y_max_val + y_min_val) / 2
    max_range = max(x_max_val - x_min_val, y_max_val - y_min_val)
    ax.set_xlim(center_x - max_range / 2 - max_range * 0.05, center_x + max_range / 2 + max_range * 0.05)
    ax.set_ylim(center_y - max_range / 2 - max_range * 0.05, center_y + max_range / 2 + max_range * 0.05)

    use_annotation_bounds = bool(params.get("render_2d_use_annotation_bounds", False))
    content_bounds = (x_min_val, x_max_val, y_min_val, y_max_val)
    if use_annotation_bounds:
        # Two passes: first pass estimates text extents, second stabilizes after x/y limits change.
        for _ in range(2):
            xmin, xmax, ymin, ymax = _compute_annotated_data_bounds()
            w_box = max(1e-6, xmax - xmin)
            h_box = max(1e-6, ymax - ymin)
            span = max(w_box, h_box)
            pad = span * 0.03
            cx = (xmin + xmax) / 2
            cy = (ymin + ymax) / 2
            span_p = span + 2 * pad
            ax.set_xlim(cx - span_p / 2, cx + span_p / 2)
            ax.set_ylim(cy - span_p / 2, cy + span_p / 2)
            content_bounds = (xmin, xmax, ymin, ymax)

    view_xmin, view_xmax = ax.get_xlim()
    view_ymin, view_ymax = ax.get_ylim()
    params["_render_2d_bounds"] = {
        "content_xmin": float(content_bounds[0]),
        "content_xmax": float(content_bounds[1]),
        "content_ymin": float(content_bounds[2]),
        "content_ymax": float(content_bounds[3]),
        "view_xmin": float(view_xmin),
        "view_xmax": float(view_xmax),
        "view_ymin": float(view_ymin),
        "view_ymax": float(view_ymax),
    }

    export_format = str(output_format or params.get("render_2d_format", "png")).lower()
    if export_format not in ("png", "svg"):
        export_format = "png"

    tight_bbox = bool(params.get("render_2d_tight_bbox", True))
    buf = BytesIO()
    if tight_bbox:
        plt.tight_layout()
        save_kwargs = {"format": export_format, "bbox_inches": "tight"}
    else:
        # Deterministic canvas for PDF scale control: no auto-cropping by content.
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        save_kwargs = {"format": export_format}
    if export_format == "png":
        save_kwargs["dpi"] = dpi
    plt.savefig(buf, **save_kwargs)
    plt.close(fig)
    mime = "image/svg+xml" if export_format == "svg" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(buf.getbuffer()).decode('ascii')}"
