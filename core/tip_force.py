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

    if shape != "round":
        return unsupported

    base_s7 = None
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
