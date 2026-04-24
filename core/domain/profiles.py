import numpy as np


def get_concave_profile(rho_arr, rc_sphere, dc):
    z_prof = np.zeros_like(rho_arr)
    if rc_sphere <= 0 or dc <= 0:
        return z_prof
    lim = np.sqrt(max(0, rc_sphere**2 - (rc_sphere - dc) ** 2))
    mask = rho_arr <= lim
    z_prof[mask] = np.sqrt(np.maximum(0, rc_sphere**2 - rho_arr[mask] ** 2)) - (rc_sphere - dc)
    return np.maximum(0, z_prof)


def get_cbe_profile(rho_arr, rc, dc, db, angle_deg):
    z_prof = np.zeros_like(rho_arr)
    if rc <= 0 or dc <= 0:
        return z_prof
    alpha = np.radians(angle_deg)
    if alpha <= 0 or alpha >= np.pi / 2:
        return z_prof

    tan_a = np.tan(alpha)
    db = min(max(0.0, db), dc)
    w_b = db / tan_a if tan_a > 0 else 0.0
    r_in = max(0.0, rc - w_b)
    hc = dc - db

    mask_bevel = (rho_arr > r_in) & (rho_arr <= rc)
    mask_cup = rho_arr <= r_in

    if np.any(mask_bevel):
        z_prof[mask_bevel] = (rc - rho_arr[mask_bevel]) * tan_a
    if np.any(mask_cup):
        if hc > 0:
            rc_inner = (r_in**2 + hc**2) / (2 * hc)
            z_prof[mask_cup] = db + np.sqrt(np.maximum(0, rc_inner**2 - rho_arr[mask_cup] ** 2)) - (rc_inner - hc)
        else:
            z_prof[mask_cup] = db
    return np.maximum(0, z_prof)


def get_ffre_profile(rho_arr, span, dc, r_edge):
    z_prof = np.zeros_like(rho_arr)
    if span <= 0 or dc <= 0:
        return z_prof
    r_edge = max(dc + 1e-6, r_edge)
    dx_curve = np.sqrt(max(0.0, r_edge**2 - (r_edge - dc) ** 2))
    flat_span = max(0.0, span - dx_curve)
    mask_flat = rho_arr <= flat_span
    mask_edge = (rho_arr > flat_span) & (rho_arr <= span)
    z_prof[mask_flat] = dc
    z_prof[mask_edge] = (dc - r_edge) + np.sqrt(np.maximum(0, r_edge**2 - (rho_arr[mask_edge] - flat_span) ** 2))
    return np.maximum(0, z_prof)


def get_ffbe_profile(rho_arr, span, dc, r_blend, angle_deg):
    z_prof = np.zeros_like(rho_arr)
    if span <= 0 or dc <= 0:
        return z_prof
    alpha = np.radians(angle_deg)
    if alpha <= 0 or alpha >= np.pi / 2:
        return z_prof

    tan_a = np.tan(alpha)
    sin_a = np.sin(alpha)
    r_blend = min(max(0.0, r_blend), dc)
    inset = (dc - r_blend) / tan_a + (r_blend / sin_a if sin_a > 0 else 0.0)
    x_center = max(0.0, span - inset)
    x_tan = x_center + r_blend * sin_a if x_center > 0 else span - dc / tan_a

    mask_flat = rho_arr <= x_center
    mask_blend = (rho_arr > x_center) & (rho_arr <= x_tan)
    mask_bevel = (rho_arr > x_tan) & (rho_arr <= span)

    z_prof[mask_flat] = dc
    z_prof[mask_blend] = (dc - r_blend) + np.sqrt(np.maximum(0, r_blend**2 - (rho_arr[mask_blend] - x_center) ** 2))
    z_prof[mask_bevel] = (span - rho_arr[mask_bevel]) * tan_a
    return np.maximum(0, z_prof)


def get_compound_profile(x_arr, r1, r2, dc, span):
    z1 = dc - r1
    if span <= 0 or r1 <= 0 or r2 <= 0:
        return np.zeros_like(x_arr)
    k = ((r1 - r2) ** 2 - r2**2 + span**2 - z1**2) / 2.0
    m = (k / span) - span
    n = z1 / span
    a, b, c = n**2 + 1.0, 2 * m * n, m**2 - r2**2
    discr = b**2 - 4 * a * c
    if discr < 0:
        return np.maximum(0, dc * (1 - (x_arr / max(1e-6, span)) ** 2))

    zc = (-b + np.sqrt(discr)) / (2 * a)
    xc = (k + z1 * zc) / span
    xt = xc * r1 / (r1 - r2) if r1 != r2 else span
    x_abs = np.abs(x_arr)

    z_prof = np.zeros_like(x_arr)
    mask_center = x_abs <= xt
    mask_edge = (x_abs > xt) & (x_abs <= span)
    z_prof[mask_center] = z1 + np.sqrt(np.maximum(0, r1**2 - x_abs[mask_center] ** 2))
    z_prof[mask_edge] = zc + np.sqrt(np.maximum(0, r2**2 - (x_abs[mask_edge] - xc) ** 2))
    return np.maximum(0, z_prof)


def _require_params(params, keys):
    missing = [k for k in keys if k not in params or params[k] is None]
    if missing:
        raise ValueError(f"Отсутствует параметр(ы): {', '.join(missing)}")


def eval_profile_1d(rho, params, span, dc):
    _require_params(params, ["profile"])
    profile = params["profile"]
    if profile in ("compound", "modified_oval"):
        _require_params(params, ["R_maj_maj", "R_maj_min"])
        return get_compound_profile(rho, params["R_maj_maj"], params["R_maj_min"], dc, span)
    if profile == "cbe":
        _require_params(params, ["Bev_D", "Bev_A"])
        return get_cbe_profile(rho, span, dc, params["Bev_D"], params["Bev_A"])
    if profile == "ffre":
        _require_params(params, ["R_edge"])
        return get_ffre_profile(rho, span, dc, params["R_edge"])
    if profile == "ffbe":
        _require_params(params, ["Blend_R", "Bev_A"])
        return get_ffbe_profile(rho, span, dc, params["Blend_R"], params["Bev_A"])
    _require_params(params, ["Rc_min"])
    return get_concave_profile(rho, params["Rc_min"], dc)
