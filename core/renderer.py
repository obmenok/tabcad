import base64
from io import BytesIO

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc

from core.engine import get_1d_z_engine, get_compound_profile

DIM_LINE_WIDTH, C_TEXT, ARROW_LENGTH = 0.6, "#9467bd", 10.0
ARR_STYLE_DOUBLE = "<|-|>,head_length=1,head_width=0.175"
ARR_STYLE_SINGLE = "-|>,head_length=1,head_width=0.175"


def p_get(params, key, default):
    val = params.get(key)
    return val if val is not None else default


def draw_ext(ax, px1, py1, px2, py2, dx, dy, text, offset=(0, 0)):
    ex1, ey1 = px1 + dx, py1 + dy
    ex2, ey2 = px2 + dx, py2 + dy
    sgx = np.sign(dx) if dx != 0 else 0
    sgy = np.sign(dy) if dy != 0 else 0
    ax.plot([px1, ex1 + sgx * 0.5], [py1, ey1 + sgy * 0.5], "k-", lw=DIM_LINE_WIDTH)
    ax.plot([px2, ex2 + sgx * 0.5], [py2, ey2 + sgy * 0.5], "k-", lw=DIM_LINE_WIDTH)
    ax.annotate(
        "",
        xy=(ex1, ey1),
        xytext=(ex2, ey2),
        arrowprops=dict(arrowstyle=ARR_STYLE_DOUBLE, color="black", lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH),
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


def draw_ext_outside(ax, px1, py1, px2, py2, dx, dy, text):
    ex1, ey1 = px1 + dx, py1 + dy
    ex2, ey2 = px2 + dx, py2 + dy
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
        arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color="black", lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH),
    )
    ax.annotate(
        "",
        xy=(ex2, ey2),
        xytext=(ex2 + ux * 3, ey2 + uy * 3),
        arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color="black", lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH),
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


def draw_pointer(ax, p_target, p_text, text):
    ax.annotate(
        text,
        xy=p_target,
        xytext=p_text,
        arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color="black", lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH),
        color=C_TEXT,
        ha="center",
        va="center",
        fontsize=9,
        bbox=dict(facecolor="#ffffff", edgecolor="none", pad=0.5),
    )


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


def _shape_meta(params):
    shape = p_get(params, "shape", "capsule")
    is_modified = bool(p_get(params, "is_modified", False))
    w_val = max(0.1, p_get(params, "W", 9.2))
    l_val = max(0.1, p_get(params, "L", 18.3))
    if shape == "round":
        l_val = w_val
    if l_val < w_val:
        l_val = w_val
    land = max(0.0, p_get(params, "Land", 0.08))
    re = min(max(0.01, p_get(params, "Re", w_val / 2 - 0.01)), w_val / 2 - 0.01)
    rs = max(l_val / 2 + 0.01, p_get(params, "Rs", 15.0))
    return shape, is_modified, w_val, l_val, land, re, rs


def _major_profile_x(x_1d, params, shape, is_modified, l_val, w_val, land, dc):
    if shape == "round":
        span = max(0.001, w_val / 2 - land)
        return get_1d_z_engine(np.abs(x_1d), params, span, dc)
    if shape == "capsule":
        l_flat = max(0, l_val - w_val)
        span = max(0.001, w_val / 2 - land)
        rho = np.maximum(0, np.abs(x_1d) - l_flat / 2)
        return get_1d_z_engine(rho, params, span, dc)
    span = max(0.001, l_val / 2 - land)
    if shape == "oval" and p_get(params, "profile", "concave") == "concave":
        # For oval concave, major side view must use major cup radius from source logic.
        params_major = dict(params)
        params_major["Rc_min"] = p_get(params, "Rc_maj", p_get(params, "Rc_min", 8.8))
        return get_1d_z_engine(np.abs(x_1d), params_major, span, dc)
    return get_1d_z_engine(np.abs(x_1d), params, span, dc)


def _minor_profile_y(y_1d, params, w_val, land, dc):
    span = max(0.001, w_val / 2 - land)
    if p_get(params, "shape", "") == "oval" and p_get(params, "profile", "") == "compound":
        return get_compound_profile(
            np.abs(y_1d),
            p_get(params, "R_min_maj", 12.7),
            p_get(params, "R_min_min", 3.81),
            dc,
            span,
        )
    return get_1d_z_engine(np.abs(y_1d), params, span, dc)


def apply_1d_groove(x_1d, z_surf, params, edge_rad):
    b_type = p_get(params, "b_type", "none")
    b_depth = p_get(params, "b_depth", 0.0)
    b_angle = p_get(params, "b_angle", 90.0)
    b_ri = p_get(params, "b_Ri", 0.06)
    dc = p_get(params, "Dc", 1.5)

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


def render_tablet(mesh_data, params):
    shape, is_modified, w_val, l_val, land, re, rs = _shape_meta(params)
    hb = p_get(params, "Hb", 2.54)
    dc = p_get(params, "Dc", 1.5)
    tt = p_get(params, "Tt", hb + 2 * dc)
    profile = p_get(params, "profile", "concave")
    b_type = p_get(params, "b_type", "none")
    b_depth = p_get(params, "b_depth", 0.0)
    b_angle = p_get(params, "b_angle", 90.0)
    b_ri = p_get(params, "b_Ri", 0.06)
    bev_a = p_get(params, "Bev_A", 40.0)
    r_edge = p_get(params, "R_edge", 6.35)
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
        ax.plot(x_out + cx_top, y_out + cy_top, "k-", linewidth=1.2)
        r_c = max(0.01, w_val / 2 - land)
        if land > 0:
            x_in, y_in = get_circle_contour(r_c)
            ax.plot(x_in + cx_top, y_in + cy_top, "k-", linewidth=0.6)
        if profile == "ffre":
            r_edge = p_get(params, "R_edge", 6.35)
            dx_curve = np.sqrt(max(0.0, r_edge**2 - (r_edge - dc) ** 2))
            flat_rad = max(0.0, r_c - dx_curve)
            if flat_rad > 0.05:
                x_flat, y_flat = get_circle_contour(flat_rad)
                ax.plot(x_flat + cx_top, y_flat + cy_top, "k--", linewidth=0.6)
        elif profile == "ffbe":
            r_blend = max(0.0, min(p_get(params, "Blend_R", 0.38), dc))
            alpha_rad = np.radians(p_get(params, "Bev_A", 30.0))
            if 1e-6 < alpha_rad < (np.pi / 2 - 1e-6):
                tan_a = np.tan(alpha_rad)
                sin_a = np.sin(alpha_rad)
                if abs(tan_a) > 1e-9 and abs(sin_a) > 1e-9:
                    d_inset = (dc - r_blend) / tan_a + r_blend / sin_a
                    flat_rad = max(0.0, r_c - d_inset)
                    if flat_rad > 0.05:
                        x_flat, y_flat = get_circle_contour(flat_rad)
                        ax.plot(x_flat + cx_top, y_flat + cy_top, "k--", linewidth=0.6)
        draw_ext(ax, cx_top - w_val / 2, cy_top + w_val / 2, cx_top - w_val / 2, cy_top - w_val / 2, -4.5, 0, f"{w_val:g}\nDiameter")
    elif shape == "capsule" and not is_modified:
        x_out, y_out = get_capsule_contour(l_val, w_val)
        ax.plot(y_out + cx_top, x_out + cy_top, "k-", linewidth=1.2)
        if land > 0:
            x_in, y_in = get_capsule_contour(max(0.1, l_val - 2 * land), max(0.1, w_val - 2 * land))
            ax.plot(y_in + cx_top, x_in + cy_top, "k-", linewidth=0.6)
        if profile == "ffre":
            r_c = max(0.01, w_val / 2 - land)
            r_edge = max(0.0, p_get(params, "R_edge", 6.35))
            dx_curve = np.sqrt(max(0.0, r_edge**2 - (r_edge - dc) ** 2))
            r_flat = max(0.0, r_c - dx_curve)
            if r_flat > 0.05:
                flat_l = l_flat + 2 * r_flat
                flat_w = 2 * r_flat
                x_flat, y_flat = get_capsule_contour(flat_l, flat_w)
                ax.plot(y_flat + cx_top, x_flat + cy_top, "k--", linewidth=0.6)
        elif profile == "ffbe":
            r_c = max(0.01, w_val / 2 - land)
            r_blend = max(0.0, min(p_get(params, "Blend_R", 0.38), dc))
            alpha_rad = np.radians(p_get(params, "Bev_A", 30.0))
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
                        ax.plot(y_flat + cx_top, x_flat + cy_top, "k--", linewidth=0.6)
        draw_ext(ax, cx_top - w_val / 2, cy_top + l_val / 2, cx_top + w_val / 2, cy_top + l_val / 2, 0, 4, f"{w_val:g}\nMinor Axis")
        draw_ext(ax, cx_top - w_val / 2, cy_top - l_val / 2, cx_top - w_val / 2, cy_top + l_val / 2, -4.5, 0, f"{l_val:g}\nMajor Axis")
    else:
        x_out, y_out = get_oval_contour(l_val, w_val, re, rs)
        ax.plot(y_out + cx_top, x_out + cy_top, "k-", linewidth=1.2)
        if land > 0 and re > land and rs > land:
            x_in, y_in = get_oval_contour(l_val - 2 * land, w_val - 2 * land, re - land, rs - land)
            ax.plot(y_in + cx_top, x_in + cy_top, "k-", linewidth=0.6)
        l_c_oval = max(0.001, l_val / 2 - land)
        w_c_oval = max(0.001, w_val / 2 - land)
        if profile == "ffre":
            r_edge_oval = max(0.0, p_get(params, "R_edge", 6.35))
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
                    # Source uses solid contour for this line.
                    ax.plot(y_flat_cont + cx_top, x_flat_cont + cy_top, "k-", linewidth=0.6)
                    oval_ref_flat_side = 2 * l_flat_half
                    oval_ref_flat_front = 2 * w_flat_half
        elif profile == "ffbe":
            r_blend_oval = max(0.0, min(p_get(params, "Blend_R", 0.38), dc))
            alpha_oval = np.radians(p_get(params, "Bev_A", 30.0))
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
                idx = np.argmin(np.abs(y_grid - x_ti))
                cond = (z - z_groove)[idx, :]
                if b_type == "standard":
                    # Match Natoli source logic: for Standard bisect clip by groove floor
                    # so inner longitudinal lines stop at triangular ends.
                    cond = np.minimum(cond, z_groove[idx, :])
                cond = np.where(mask_cup[idx, :], cond, -1.0)
                v_idx = np.where(cond >= 0)[0]
                if len(v_idx) > 0:
                    x_s, x_e = x_grid[v_idx[0]], x_grid[v_idx[-1]]
                    ax.plot([x_s + cx_top, x_e + cx_top], [x_ti + cy_top, x_ti + cy_top], "k-", lw=0.6)
                    ax.plot([x_s + cx_top, x_e + cx_top], [-x_ti + cy_top, -x_ti + cy_top], "k-", lw=0.6)
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
    z_up_maj_base = _major_profile_x(x_maj, params, shape, is_modified, l_val, w_val, land, dc)
    z_up_maj = apply_1d_groove(x_maj, z_up_maj_base, params, max(0.001, span))
    z_down_maj = z_up_maj_base

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
    ax.plot(t_prof + cx_side, l_prof + cy_side, "k-", linewidth=1.2)
    ax.plot([-hb / 2 + cx_side, -hb / 2 + cx_side], [-l_side / 2 + cy_side, l_side / 2 + cy_side], "k-", linewidth=1.2)
    ax.plot([hb / 2 + cx_side, hb / 2 + cx_side], [-l_side / 2 + cy_side, l_side / 2 + cy_side], "k-", linewidth=1.2)
    draw_ext_outside(ax, cx_side + hb / 2, cy_side + l_side / 2, cx_side + hb / 2 + dc, cy_side + l_side / 2, 0, 4, f"{dc:g}\nCup Depth")
    if profile == "cbe":
        bev_d = p_get(params, "Bev_D", 0.51)
        if bev_d > 0:
            draw_ext_outside(ax, cx_side + hb / 2, cy_side + l_side / 2, cx_side + hb / 2 + bev_d, cy_side + l_side / 2, 0, 2, f"{bev_d:g}\nBevel Depth")
    draw_ext_outside(ax, cx_side - hb / 2, cy_side - l_side / 2, cx_side + hb / 2, cy_side - l_side / 2, 0, -4, f"{hb:g}\nBelly Band")
    if shape == "capsule" and l_flat > 0:
        ref_flat_side = l_flat
        if profile == "ffre":
            r_c_caps = max(0.01, w_val / 2 - land)
            r_edge_caps = max(0.0, p_get(params, "R_edge", 6.35))
            dx_curve = np.sqrt(max(0.0, r_edge_caps**2 - (r_edge_caps - dc) ** 2))
            capsule_r_flat = max(0.0, r_c_caps - dx_curve)
            ref_flat_side = l_flat + 2 * capsule_r_flat
        elif profile == "ffbe":
            r_c_caps = max(0.01, w_val / 2 - land)
            r_blend_caps = max(0.0, min(p_get(params, "Blend_R", 0.38), dc))
            alpha_caps = np.radians(p_get(params, "Bev_A", 30.0))
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
        rc_maj = p_get(params, "Rc_maj", p_get(params, "Rc_min", 8.8))
        p_idx = np.argmin(np.abs(x_maj - (-l_side / 4)))
        pt_surf = z_up_maj[p_idx] + hb / 2
        pt_len = x_maj[p_idx]
        draw_pointer(ax, (pt_surf + cx_side, pt_len + cy_side), (pt_surf + cx_side + 4, pt_len + cy_side - l_side / 4), f"{rc_maj:g}\nCup Radius\nMajor")
    elif shape == "oval" and profile in ("modified_oval", "compound"):
        r_maj_maj = p_get(params, "R_maj_maj", 88.9)
        r_maj_min = p_get(params, "R_maj_min", 6.35)
        l_c = max(0.001, l_val / 2 - land)
        x_maj_pt = l_c * 0.30
        z_maj_pt = get_compound_profile(np.array([x_maj_pt]), r_maj_maj, r_maj_min, dc, l_c)[0]
        target_maj = (cx_side + hb / 2 + z_maj_pt, cy_side + x_maj_pt)
        text_maj = (cx_side + hb / 2 + z_maj_pt + 7, cy_side + x_maj_pt + 2)
        draw_pointer(ax, target_maj, text_maj, f"{r_maj_maj:g}\nMajor Major\nRadius")

        x_min_pt = l_c * 0.85
        z_min_pt = get_compound_profile(np.array([x_min_pt]), r_maj_maj, r_maj_min, dc, l_c)[0]
        target_min = (cx_side + hb / 2 + z_min_pt, cy_side - x_min_pt)
        text_min = (cx_side + hb / 2 + z_min_pt + 7, cy_side - x_min_pt + 2.5)
        draw_pointer(ax, target_min, text_min, f"{r_maj_min:g}\nMajor Minor\nRadius")

    span_front = max(0.001, w_val / 2 - land)
    y_min_cup = np.linspace(-span_front, span_front, 400)
    z_up_min = _minor_profile_y(y_min_cup, params, w_val, land, dc)
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

    if land > 0:
        l_land_coord = span_front
        ax.plot([cx_front + l_land_coord, cx_front + l_land_coord], [cy_front + tt / 2, cy_front + tt / 2 + 2.5], "k-", lw=DIM_LINE_WIDTH)
        ax.plot([cx_front + w_val / 2, cx_front + w_val / 2], [cy_front + tt / 2, cy_front + tt / 2 + 2.5], "k-", lw=DIM_LINE_WIDTH)
        ax.annotate(
            "",
            xy=(cx_front + l_land_coord, cy_front + tt / 2 + 2),
            xytext=(cx_front + l_land_coord - 2.5, cy_front + tt / 2 + 2),
            arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color="black", lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH),
        )
        ax.annotate(
            "",
            xy=(cx_front + w_val / 2, cy_front + tt / 2 + 2),
            xytext=(cx_front + w_val / 2 + 2.5, cy_front + tt / 2 + 2),
            arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color="black", lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH),
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
            fontsize=9,
            bbox=dict(facecolor="#ffffff", edgecolor="none", pad=0.5),
        )

    if profile == "modified_oval" and shape == "oval":
        rc_min = p_get(params, "Rc_min", 8.8)
        draw_pointer(ax, (cx_front, cy_front + tt / 2), (cx_front - w_val / 4, cy_front + tt / 2 + 4), f"{rc_min:g}\nCup Radius\nMinor")
    elif profile == "compound" and shape == "oval":
        r_min_maj = p_get(params, "R_min_maj", 12.7)
        r_min_min = p_get(params, "R_min_min", 3.81)
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
        r_maj_maj = p_get(params, "R_maj_maj", 88.9)
        r_maj_min = p_get(params, "R_maj_min", 6.35)
        x_min_pt = span_front * 0.8
        z_min_pt = get_compound_profile(np.array([x_min_pt]), r_maj_maj, r_maj_min, dc, span_front)[0]
        draw_pointer(ax, (cx_front - x_min_pt, cy_front + hb / 2 + z_min_pt), (cx_front - x_min_pt - w_val / 6, cy_front + hb / 2 + z_min_pt + 5), f"{r_maj_min:g}\nMinor Radius")
        if shape == "round":
            x_maj_pt = span_front * 0.2
            z_maj_pt = get_compound_profile(np.array([x_maj_pt]), r_maj_maj, r_maj_min, dc, span_front)[0]
            draw_pointer(ax, (cx_front + x_maj_pt, cy_front + hb / 2 + z_maj_pt), (cx_front + x_maj_pt + 0.5, cy_front + hb / 2 + z_maj_pt + 5), f"{r_maj_maj:g}\nMajor Radius")
    elif profile == "ffbe":
        r_blend = max(0.0, min(p_get(params, "Blend_R", 0.38), dc))
        alpha_rad = np.radians(p_get(params, "Bev_A", 30.0))
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
            r_blend_caps = max(0.0, min(p_get(params, "Blend_R", 0.38), dc))
            alpha_caps = np.radians(p_get(params, "Bev_A", 30.0))
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
        rc_min = p_get(params, "Rc_min", 8.8)
        draw_pointer(ax, (cx_front, cy_front + hb / 2 + dc), (cx_front - w_val / 4, cy_front + hb / 2 + dc + 4), f"{rc_min:g}\nCup Radius")

    x_min_val, x_max_val = cx_side - tt / 2 - 12, cx_top + w_val / 2 + 15
    y_min_val, y_max_val = cy_front - tt / 2 - 8, cy_top + l_val / 2 + 8
    center_x, center_y = (x_max_val + x_min_val) / 2, (y_max_val + y_min_val) / 2
    max_range = max(x_max_val - x_min_val, y_max_val - y_min_val)
    ax.set_xlim(center_x - max_range / 2 - max_range * 0.05, center_x + max_range / 2 + max_range * 0.05)
    ax.set_ylim(center_y - max_range / 2 - max_range * 0.05, center_y + max_range / 2 + max_range * 0.05)

    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    return f"data:image/png;base64,{base64.b64encode(buf.getbuffer()).decode('ascii')}"
