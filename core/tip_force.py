import math
from typing import Optional


TSM_TABLE_19 = {
    0.007: 0.463,
    0.008: 0.432,
    0.009: 0.405,
    0.010: 0.383,
    0.011: 0.364,
    0.012: 0.348,
    0.013: 0.333,
    0.014: 0.321,
    0.015: 0.309,
    0.016: 0.299,
    0.017: 0.289,
    0.018: 0.280,
    0.019: 0.272,
    0.020: 0.265,
    0.021: 0.258,
    0.022: 0.252,
    0.023: 0.246,
    0.024: 0.241,
    0.025: 0.235,
}

STEEL_FACTORS = {
    "S7": 1.0,
    "D2": 0.8,
}


def get_k_factor(land_mm: float) -> float:
    land_in = land_mm / 25.4
    if land_in <= 0.002:
        return 4.6665
    if land_in <= 0.003:
        return 4.6665 + (land_in - 0.002) * (-148.1)
    if land_in <= 0.004:
        return 4.5184 + (land_in - 0.003) * (-132.3)
    if land_in <= 0.005:
        return 4.3861 + (land_in - 0.004) * (-119.6)
    if land_in <= 0.006:
        return 4.2665 + (land_in - 0.005) * (-109.0)
    if land_in <= 0.007:
        return 4.1575 + (land_in - 0.006) * (-100.2)
    if land_in <= 0.008:
        return 4.0573 + (land_in - 0.007) * (-92.0)
    return 3.9653


def _safe_float(value, fallback: float = 0.0) -> float:
    if value is None:
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _has_bisect(params: dict) -> bool:
    return params.get("b_type", "none") != "none"


def _force_round_ffbe(params: dict) -> Optional[float]:
    d_mm = _safe_float(params.get("W"))
    depth_mm = _safe_float(params.get("Dc"))
    if d_mm <= 0 or depth_mm <= 0:
        return None

    area_mm2 = math.pi / 4.0 * (d_mm ** 2)
    depth_in = depth_mm / 25.4
    depth_in_limited = round(max(0.007, min(depth_in, 0.025)), 3)
    pressure_p = TSM_TABLE_19.get(depth_in_limited)
    if pressure_p is None:
        return None
    return area_mm2 * pressure_p * 1.35


def _force_round_concave(params: dict) -> Optional[float]:
    d_mm = _safe_float(params.get("W"))
    depth_mm = _safe_float(params.get("Dc"))
    land_mm = _safe_float(params.get("Land"))
    if d_mm <= 0 or depth_mm <= 0:
        return None

    area_mm2 = math.pi / 4.0 * (d_mm ** 2)
    sf_limited = max(0.0, min(depth_mm / d_mm, 0.35))
    pressure_p = 10 ** (0.3775 - get_k_factor(land_mm) * sf_limited)
    return area_mm2 * pressure_p * 1.35


def _force_round_edge_radius(params: dict, radius_key: str) -> Optional[float]:
    d_mm = _safe_float(params.get("W"))
    depth_mm = _safe_float(params.get("Dc"))
    land_mm = _safe_float(params.get("Land"))
    edge_radius_mm = _safe_float(params.get(radius_key))
    if d_mm <= 0 or depth_mm <= 0 or edge_radius_mm <= 0 or depth_mm > edge_radius_mm:
        return None

    area_mm2 = math.pi / 4.0 * (d_mm ** 2)
    term = 2 * edge_radius_mm * depth_mm - depth_mm ** 2
    if term <= 0:
        return None

    d_cap = 2 * math.sqrt(term)
    if d_cap <= 0:
        return None

    sf_limited = max(0.0, min(depth_mm / d_cap, 0.35))
    pressure_p = 10 ** (0.3775 - get_k_factor(land_mm) * sf_limited)
    return area_mm2 * pressure_p * 1.35


def _force_round_cbe(params: dict) -> Optional[float]:
    d_mm = _safe_float(params.get("W"))
    bevel_depth_mm = _safe_float(params.get("Bev_D"))
    land_mm = _safe_float(params.get("Land"))
    angle_deg = _safe_float(params.get("Bev_A"))
    if d_mm <= 0 or bevel_depth_mm <= 0:
        return None

    intercept = 0.2987
    coef_d = 2.0446
    coef_angle = -0.02133
    coef_depth = -0.2132
    coef_land = 1.4361

    log_f = (
        intercept
        + coef_d * math.log10(d_mm)
        + coef_angle * angle_deg
        + coef_depth * bevel_depth_mm
        + coef_land * land_mm
    )
    return 10 ** log_f


def _capsule_standard_area_mm2(params: dict) -> Optional[float]:
    w_mm = _safe_float(params.get("W"))
    l_mm = _safe_float(params.get("L"))
    if w_mm <= 0 or l_mm <= 0:
        return None
    l_mm = max(l_mm, w_mm)
    rect_len = max(0.0, l_mm - w_mm)
    return rect_len * w_mm + math.pi / 4.0 * (w_mm ** 2)


def _capsule_area_mm2(params: dict) -> Optional[float]:
    w_mm = _safe_float(params.get("W"))
    l_mm = _safe_float(params.get("L"))
    if w_mm <= 0 or l_mm <= 0:
        return None
    l_mm = max(l_mm, w_mm)
    if bool(params.get("is_modified")):
        re_mm = _safe_float(params.get("Re"))
        rs_mm = _safe_float(params.get("Rs"))
        if re_mm > 0 and rs_mm > 0:
            xe = l_mm / 2.0 - re_mm
            ys = w_mm / 2.0 - rs_mm
            gamma = math.atan2(abs(ys), max(1e-9, xe))
            x_tan = xe + re_mm * math.cos(gamma)

            def arc_area(x_val: float, radius: float, y0: float) -> float:
                root = math.sqrt(max(0.0, radius ** 2 - x_val ** 2))
                return 0.5 * (
                    x_val * root
                    + radius ** 2 * math.asin(max(-1.0, min(1.0, x_val / radius)))
                ) + y0 * x_val

            def end_arc_area(u_val: float, radius: float) -> float:
                root = math.sqrt(max(0.0, radius ** 2 - u_val ** 2))
                return 0.5 * (
                    u_val * root
                    + radius ** 2 * math.asin(max(-1.0, min(1.0, u_val / radius)))
                )

            return 4.0 * (
                (arc_area(x_tan, rs_mm, ys) - arc_area(0.0, rs_mm, ys))
                + (end_arc_area(re_mm, re_mm) - end_arc_area(x_tan - xe, re_mm))
            )
    return _capsule_standard_area_mm2(params)


def _capsule_equivalent_diameter_mm(params: dict) -> Optional[float]:
    area_mm2 = _capsule_standard_area_mm2(params)
    if area_mm2 is None or area_mm2 <= 0:
        return None
    return math.sqrt(4.0 * area_mm2 / math.pi)


def _force_capsule_concave(params: dict) -> Optional[float]:
    area_mm2 = _capsule_area_mm2(params)
    w_mm = _safe_float(params.get("W"))
    depth_mm = _safe_float(params.get("Dc"))
    land_mm = _safe_float(params.get("Land"))
    if area_mm2 is None or w_mm <= 0 or depth_mm <= 0:
        return None

    sf_limited = max(0.0, min(depth_mm / w_mm, 0.35))
    pressure_p = 10 ** (0.3775 - get_k_factor(land_mm) * sf_limited)
    return area_mm2 * pressure_p * 1.35


def _force_capsule_edge_radius(params: dict, radius_key: str) -> Optional[float]:
    area_mm2 = _capsule_area_mm2(params)
    w_mm = _safe_float(params.get("W"))
    depth_mm = _safe_float(params.get("Dc"))
    land_mm = _safe_float(params.get("Land"))
    edge_radius_mm = _safe_float(params.get(radius_key))
    if area_mm2 is None or w_mm <= 0 or depth_mm <= 0 or edge_radius_mm <= 0:
        return None
    if depth_mm > edge_radius_mm:
        return None

    term = 2 * edge_radius_mm * depth_mm - depth_mm ** 2
    if term <= 0:
        return None

    d_cap = 2 * math.sqrt(term)
    if d_cap <= 0:
        return None

    sf_limited = max(0.0, min(depth_mm / d_cap, 0.35))
    pressure_p = 10 ** (0.3775 - get_k_factor(land_mm) * sf_limited)
    return area_mm2 * pressure_p * 1.35


def _force_capsule_ffbe(params: dict) -> Optional[float]:
    area_mm2 = _capsule_area_mm2(params)
    depth_mm = _safe_float(params.get("Dc"))
    if area_mm2 is None or depth_mm <= 0:
        return None

    depth_in = depth_mm / 25.4
    depth_in_limited = round(max(0.007, min(depth_in, 0.025)), 3)
    pressure_p = TSM_TABLE_19.get(depth_in_limited)
    if pressure_p is None:
        return None
    return area_mm2 * pressure_p * 1.35


def _force_capsule_cbe(params: dict) -> Optional[float]:
    d_eq_mm = _capsule_equivalent_diameter_mm(params)
    bevel_depth_mm = _safe_float(params.get("Bev_D"))
    land_mm = _safe_float(params.get("Land"))
    angle_deg = _safe_float(params.get("Bev_A"))
    if d_eq_mm is None or bevel_depth_mm <= 0:
        return None

    intercept = 0.2987
    coef_d = 2.0446
    coef_angle = -0.02133
    coef_depth = -0.2132
    coef_land = 1.4361

    log_f = (
        intercept
        + coef_d * math.log10(d_eq_mm)
        + coef_angle * angle_deg
        + coef_depth * bevel_depth_mm
        + coef_land * land_mm
    )
    return 10 ** log_f


def _oval_area_mm2(params: dict) -> Optional[float]:
    w_mm = _safe_float(params.get("W"))
    l_mm = _safe_float(params.get("L"))
    if w_mm <= 0 or l_mm <= 0:
        return None
    # TSM-style conservative oval area approximation.
    return math.pi / 4.0 * w_mm * l_mm


def _force_oval_concave(params: dict) -> Optional[float]:
    area_mm2 = _oval_area_mm2(params)
    w_mm = _safe_float(params.get("W"))
    depth_mm = _safe_float(params.get("Dc"))
    land_mm = _safe_float(params.get("Land"))
    if area_mm2 is None or w_mm <= 0 or depth_mm <= 0:
        return None

    # For oval concave punches, the limiting section is governed by the minor axis.
    sf_limited = max(0.0, min(depth_mm / w_mm, 0.35))
    pressure_p = 10 ** (0.3775 - get_k_factor(land_mm) * sf_limited)
    return area_mm2 * pressure_p * 1.35


def _force_oval_edge_radius(params: dict, radius_key: str) -> Optional[float]:
    area_mm2 = _oval_area_mm2(params)
    w_mm = _safe_float(params.get("W"))
    depth_mm = _safe_float(params.get("Dc"))
    land_mm = _safe_float(params.get("Land"))
    edge_radius_mm = _safe_float(params.get(radius_key))
    if area_mm2 is None or w_mm <= 0 or depth_mm <= 0 or edge_radius_mm <= 0:
        return None
    if depth_mm > edge_radius_mm:
        return None

    term = 2 * edge_radius_mm * depth_mm - depth_mm ** 2
    if term <= 0:
        return None

    # Equivalent cup width is still governed by the local radius at the minor section.
    d_cap = 2 * math.sqrt(term)
    if d_cap <= 0:
        return None

    sf_limited = max(0.0, min(depth_mm / d_cap, 0.35))
    pressure_p = 10 ** (0.3775 - get_k_factor(land_mm) * sf_limited)
    return area_mm2 * pressure_p * 1.35


def _force_oval_ffbe(params: dict) -> Optional[float]:
    area_mm2 = _oval_area_mm2(params)
    depth_mm = _safe_float(params.get("Dc"))
    if area_mm2 is None or depth_mm <= 0:
        return None

    depth_in = depth_mm / 25.4
    depth_in_limited = round(max(0.007, min(depth_in, 0.025)), 3)
    pressure_p = TSM_TABLE_19.get(depth_in_limited)
    if pressure_p is None:
        return None
    return area_mm2 * pressure_p * 1.35


def _force_oval_cbe(params: dict) -> Optional[float]:
    w_mm = _safe_float(params.get("W"))
    l_mm = _safe_float(params.get("L"))
    bevel_depth_mm = _safe_float(params.get("Bev_D"))
    land_mm = _safe_float(params.get("Land"))
    angle_deg = _safe_float(params.get("Bev_A"))
    if w_mm <= 0 or l_mm <= 0 or bevel_depth_mm <= 0:
        return None

    # Reuse the recovered round CBE model with an oval equivalent diameter based on area.
    d_eq_mm = math.sqrt(w_mm * l_mm)

    intercept = 0.2987
    coef_d = 2.0446
    coef_angle = -0.02133
    coef_depth = -0.2132
    coef_land = 1.4361

    log_f = (
        intercept
        + coef_d * math.log10(d_eq_mm)
        + coef_angle * angle_deg
        + coef_depth * bevel_depth_mm
        + coef_land * land_mm
    )
    return 10 ** log_f


def calculate_tip_force(params: dict) -> dict:
    shape = params.get("shape")
    profile = params.get("profile")
    steel = params.get("tip_force_steel", "S7")
    if steel not in STEEL_FACTORS:
        steel = "S7"

    unsupported = {
        "supported": False,
        "steel": steel,
        "selected_force": None,
        "s7_force": None,
        "d2_force": None,
    }

    base_s7 = None
    if shape == "round":
        if profile == "ffbe":
            base_s7 = _force_round_ffbe(params)
        elif profile == "concave":
            base_s7 = _force_round_concave(params)
        elif profile == "ffre":
            base_s7 = _force_round_edge_radius(params, "R_edge")
        elif profile == "compound":
            base_s7 = _force_round_edge_radius(params, "R_maj_min")
        elif profile == "cbe":
            base_s7 = _force_round_cbe(params)
    elif shape == "capsule":
        if profile == "ffbe":
            base_s7 = _force_capsule_ffbe(params)
        elif profile == "concave":
            base_s7 = _force_capsule_concave(params)
        elif profile == "ffre":
            base_s7 = _force_capsule_edge_radius(params, "R_edge")
        elif profile == "cbe":
            base_s7 = _force_capsule_cbe(params)
    elif shape == "oval":
        if profile == "ffbe":
            base_s7 = _force_oval_ffbe(params)
        elif profile in ("concave", "modified_oval"):
            base_s7 = _force_oval_concave(params)
        elif profile == "ffre":
            base_s7 = _force_oval_edge_radius(params, "R_edge")
        elif profile == "compound":
            base_s7 = _force_oval_edge_radius(params, "R_min_min")
        elif profile == "cbe":
            base_s7 = _force_oval_cbe(params)
    else:
        return unsupported

    if base_s7 is None:
        return unsupported

    if _has_bisect(params):
        base_s7 *= 0.80

    s7_force = round(base_s7)
    d2_force = round(base_s7 * STEEL_FACTORS["D2"])
    selected_force = s7_force if steel == "S7" else d2_force

    return {
        "supported": True,
        "steel": steel,
        "selected_force": selected_force,
        "s7_force": s7_force,
        "d2_force": d2_force,
    }
