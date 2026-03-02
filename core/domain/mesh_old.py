import numpy as np

from core.domain.profiles import eval_profile_1d
from core.domain.shapes import capsule_rho, minor_span, oval_mask, oval_metrics, shape_params


def build_surface(params, x_grid, y_grid):
    shape, is_modified, w_val, l_val, land, re, rs = shape_params(params)
    dc = max(0.0, params.get("Dc", 1.5))
    x_arr, y_arr = np.meshgrid(x_grid, y_grid)

    if shape == "round":
        rc = max(0.001, w_val / 2 - land)
        rho = np.sqrt(x_arr**2 + y_arr**2)
        mask_cup = rho <= rc
        z = np.zeros_like(x_arr)
        z[mask_cup] = eval_profile_1d(rho[mask_cup], params, rc, dc)
        perimeter = np.pi * w_val
        die_hole_sa = np.pi * (w_val / 2) ** 2
        return x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa

    if shape == "capsule" and not is_modified:
        l_flat = max(0.0, l_val - w_val)
        rc = max(0.001, w_val / 2 - land)
        rho = capsule_rho(x_arr, y_arr, l_flat)
        mask_cup = rho <= rc
        z = np.zeros_like(x_arr)
        z[mask_cup] = eval_profile_1d(rho[mask_cup], params, rc, dc)
        perimeter = np.pi * w_val + 2 * l_flat
        die_hole_sa = np.pi * (w_val / 2) ** 2 + w_val * l_flat
        return x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa

    if shape == "capsule" and is_modified:
        l_flat = max(0.0, l_val - w_val)
        rc = max(0.001, w_val / 2 - land)
        base_mask = oval_mask(x_arr, y_arr, l_val, w_val, re, rs)
        if land > 0 and re > land + 1e-3 and rs > land + 1e-3:
            mask_cup = oval_mask(x_arr, y_arr, l_val - 2 * land, w_val - 2 * land, re - land, rs - land)
        else:
            mask_cup = base_mask

        rho = capsule_rho(x_arr, y_arr, l_flat)
        z = np.zeros_like(x_arr)
        z[mask_cup] = eval_profile_1d(rho[mask_cup], params, rc, dc)
        perimeter, die_hole_sa = oval_metrics(l_val, w_val, re, rs)
        return x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa

    base_mask = oval_mask(x_arr, y_arr, l_val, w_val, re, rs)
    if land > 0 and re > land + 1e-3 and rs > land + 1e-3:
        mask_cup = oval_mask(x_arr, y_arr, l_val - 2 * land, w_val - 2 * land, re - land, rs - land)
    else:
        mask_cup = base_mask

    l_c = max(0.001, l_val / 2 - land)
    w_c = max(0.001, w_val / 2 - land)
    z = np.zeros_like(x_arr)
    profile = params.get("profile", "concave")
    if profile == "concave":
        rho_norm = np.sqrt((x_arr / l_c) ** 2 + (y_arr / w_c) ** 2)
        valid = (rho_norm <= 1.0) & mask_cup
        z[valid] = dc * (1 - rho_norm[valid] ** 2)
    elif profile == "compound":
        z_l = eval_profile_1d(np.abs(x_arr), params, l_c, dc)
        params_min = dict(params)
        params_min["profile"] = "compound"
        params_min["R_maj_maj"] = params.get("R_min_maj", 12.7)
        params_min["R_maj_min"] = params.get("R_min_min", 3.81)
        z_w = eval_profile_1d(np.abs(y_arr), params_min, w_c, dc)
        z_prod = (z_l * z_w) / max(1e-6, dc)
        z[mask_cup] = z_prod[mask_cup]
    else:
        z_l = eval_profile_1d(np.abs(x_arr), params, l_c, dc)
        z_w = eval_profile_1d(np.abs(y_arr), params, w_c, dc)
        z_prod = (z_l * z_w) / max(1e-6, dc)
        z[mask_cup] = z_prod[mask_cup]
    rho = np.sqrt((x_arr / l_c) ** 2 + (y_arr / w_c) ** 2) * w_c

    perimeter, die_hole_sa = oval_metrics(l_val, w_val, re, rs)
    return x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa


def compute_bisect_width(params, depth, angle, ri):
    if depth <= 0:
        return 0.0
    dc = max(0.0, params.get("Dc", 1.5))
    span = minor_span(params)
    x_test = np.linspace(0, span, 2000)
    z_bottom = dc - depth
    alpha = np.radians(angle / 2.0)
    if alpha <= 0:
        return 0.0
    d_sharp = ri / np.sin(alpha) - ri if ri > 0 else 0
    x_ti = ri * np.sin(alpha)
    z_v = z_bottom - d_sharp + x_test / np.tan(alpha)
    z_inner = z_bottom + ri - np.sqrt(np.maximum(0, ri**2 - x_test**2))
    z_g = np.where(x_test <= x_ti, z_inner, z_v)
    z_cup = eval_profile_1d(x_test, params, span, dc)
    diff = z_cup - z_g
    crossings = np.where(np.diff(np.sign(diff)))[0]
    if len(crossings) > 0:
        idx = crossings[0]
        x1, x2 = x_test[idx], x_test[idx + 1]
        y1, y2 = diff[idx], diff[idx + 1]
        if y2 != y1:
            return round(2 * (x1 - y1 * (x2 - x1) / (y2 - y1)), 4)
    return 0.0


def compute_bisect_depth(params, target_width, angle, ri):
    if target_width <= 0:
        return 0.0
    dc = max(0.0, params.get("Dc", 1.5))
    d_min, d_max = 0.0, dc * 2.0
    for _ in range(35):
        d_mid = (d_min + d_max) / 2
        w_mid = compute_bisect_width(params, d_mid, angle, ri)
        if w_mid < target_width:
            d_min = d_mid
        else:
            d_max = d_mid
    return round((d_min + d_max) / 2, 4)


def generate_mesh(params):
    shape, _, w_val, l_val, _, _, _ = shape_params(params)
    dc = max(0.0, params.get("Dc", 1.5))

    x_grid = np.linspace(-l_val / 2, l_val / 2, 300)
    y_grid = np.linspace(-w_val / 2, w_val / 2, 300)
    x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa = build_surface(params, x_grid, y_grid)

    dx, dy = x_grid[1] - x_grid[0], y_grid[1] - y_grid[0]
    d_a = dx * dy

    z_cup_top = z.copy()
    z_groove = np.full_like(z, dc * 5.0)

    b_type = params.get("b_type", "none")
    b_depth = params.get("b_depth", 0.0) or 0.0
    if b_type != "none" and b_depth > 0:
        b_angle = params.get("b_angle", 90.0)
        b_ri = params.get("b_Ri", 0.061)
        alpha = np.radians(b_angle / 2.0)
        d_sharp = b_ri / np.sin(alpha) - b_ri if (b_ri > 0 and alpha > 0) else 0.0
        x_ti = b_ri * np.sin(alpha)

        if shape == "round":
            cut_axis, along_axis = np.abs(y_arr), np.abs(x_arr)
        else:
            cut_axis, along_axis = np.abs(x_arr), np.abs(y_arr)

        span = minor_span(params)
        profile = params.get("profile", "concave")
        # Match Natoli source logic for Oval Compound Cup:
        # groove centerline along minor axis must use minor compound radii.
        if shape == "oval" and profile == "compound":
            params_along = dict(params)
            params_along["profile"] = "compound"
            params_along["R_maj_maj"] = params.get("R_min_maj", 12.7)
            params_along["R_maj_min"] = params.get("R_min_min", 3.81)
            z_centerline = eval_profile_1d(along_axis, params_along, span, dc)
        else:
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
        z_cup_top = np.maximum(0, np.minimum(z, z_groove))

    cup_vol = np.sum(z_cup_top) * d_a
    dzdx = np.gradient(z_cup_top, dx, axis=1)
    dzdy = np.gradient(z_cup_top, dy, axis=0)
    cup_sa = np.sum(np.sqrt(1 + dzdx**2 + dzdy**2)[mask_cup]) * d_a

    land_sa = max(0.0, die_hole_sa - np.sum(mask_cup) * d_a)
    hb = params.get("Hb", 2.54)
    tablet_sa = perimeter * hb + 2 * (cup_sa + land_sa)
    tablet_vol = die_hole_sa * hb + 2 * cup_vol

    return {
        "X": x_arr,
        "Y": y_arr,
        "Z": z,
        "Z_groove": z_groove,
        "Z_cup_top": z_cup_top,
        "mask_cup": mask_cup,
        "rho": rho,
        "x_grid": x_grid,
        "y_grid": y_grid,
        "metrics": {
            "Die_Hole_SA": round(die_hole_sa, 4),
            "Cup_Volume": round(cup_vol, 4),
            "Cup_SA": round(cup_sa + land_sa, 4),
            "Perimeter": round(perimeter, 4),
            "Tablet_SA": round(tablet_sa, 4),
            "Tablet_Vol": round(tablet_vol, 4),
        },
    }
