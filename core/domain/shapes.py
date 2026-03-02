import numpy as np


def safe(value, default):
    return default if value is None else value


def calc_oval_rs(l_val, w_val, re):
    den = max(1e-6, w_val - 2 * re)
    return ((l_val / 2 - re) ** 2 + (w_val / 2) ** 2 - re**2) / den


def shape_params(params):
    shape = params.get("shape", "capsule")
    w_val = max(0.1, safe(params.get("W"), 9.2))
    l_val = max(0.1, safe(params.get("L"), 18.3))
    if shape == "round":
        l_val = w_val
    if l_val < w_val:
        l_val = w_val

    land = max(0.0, safe(params.get("Land"), 0.08))
    re = safe(params.get("Re"), w_val / 2 - 0.01)
    re = min(max(0.01, re), w_val / 2 - 0.01)
    rs = safe(params.get("Rs"), calc_oval_rs(l_val, w_val, re))
    rs = max(l_val / 2 + 0.01, rs)
    return shape, bool(params.get("is_modified", False)), w_val, l_val, land, re, rs


def minor_span(params):
    _, _, w_val, _, land, _, _ = shape_params(params)
    return max(0.001, w_val / 2 - land)


def capsule_rho(x_arr, y_arr, l_flat):
    rho = np.zeros_like(x_arr)
    mask_center = np.abs(x_arr) <= l_flat / 2
    mask_top = x_arr > l_flat / 2
    mask_bot = x_arr < -l_flat / 2
    rho[mask_center] = np.abs(y_arr[mask_center])
    rho[mask_top] = np.sqrt((x_arr[mask_top] - l_flat / 2) ** 2 + y_arr[mask_top] ** 2)
    rho[mask_bot] = np.sqrt((x_arr[mask_bot] + l_flat / 2) ** 2 + y_arr[mask_bot] ** 2)
    return rho


def oval_metrics(l_val, w_val, re, rs):
    xe = l_val / 2 - re
    ys = w_val / 2 - rs
    gamma = np.arctan2(abs(ys), max(1e-9, xe))
    perimeter = 4 * gamma * re + 2 * (np.pi - 2 * gamma) * rs
    x_tan = xe + re * np.cos(gamma)

    def arc_area(xv, rad, y0):
        return 0.5 * (xv * np.sqrt(np.maximum(0.0, rad**2 - xv**2)) + rad**2 * np.arcsin(np.clip(xv / rad, -1, 1))) + y0 * xv

    # ИСПРАВЛЕНО: убрали двойное вычитание xe
    def end_arc_area(u, rad):
        return 0.5 * (u * np.sqrt(np.maximum(0.0, rad**2 - u**2)) + rad**2 * np.arcsin(np.clip(u / rad, -1, 1)))

    die_hole_sa = 4 * ((arc_area(x_tan, rs, ys) - arc_area(0, rs, ys)) + (end_arc_area(re, re) - end_arc_area(x_tan - xe, re)))
    return perimeter, die_hole_sa


def oval_mask(x_arr, y_arr, l_val, w_val, re, rs):
    xi = np.abs(x_arr)
    yi = np.abs(y_arr)
    xe = l_val / 2 - re
    ys = w_val / 2 - rs
    gamma = np.arctan2(abs(ys), max(1e-9, xe))
    x_tan = xe + re * np.cos(gamma)
    side = (yi - ys) ** 2 + xi**2 <= rs**2
    end = yi**2 + (xi - xe) ** 2 <= re**2
    return ((xi <= x_tan) & side) | ((xi > x_tan) & end)
