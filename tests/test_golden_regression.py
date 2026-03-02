import math

from core.engine import generate_mesh
from core.reference_bridge import render_from_reference


METRIC_KEYS = ["Die_Hole_SA", "Cup_Volume", "Cup_SA", "Perimeter", "Tablet_SA", "Tablet_Vol"]


def _base_params():
    return {
        "b_type": "none",
        "b_depth": 0.0,
        "b_angle": 90.0,
        "b_Ri": 0.061,
        "Bev_D": 0.51,
        "Bev_A": 40.0,
        "R_edge": 6.35,
        "Blend_R": 0.38,
        "R_maj_maj": 88.9,
        "R_maj_min": 6.35,
        "Rc_min": 8.8,
        "Rc_maj": 21.587,
    }


CASES = [
    # Round
    (
        "round_concave",
        {"shape": "round", "profile": "concave", "is_modified": False, "W": 7.94, "L": 7.94, "Dc": 0.64, "Land": 0.08, "Hb": 2.54, "Tt": 3.81, "Rc_min": 12.25},
        0.03,
    ),
    (
        "round_compound",
        {"shape": "round", "profile": "compound", "is_modified": False, "W": 7.94, "L": 7.94, "Dc": 0.64, "Land": 0.08, "Hb": 2.54, "Tt": 3.81},
        0.02,
    ),
    (
        "round_cbe",
        {"shape": "round", "profile": "cbe", "is_modified": False, "W": 7.94, "L": 7.94, "Dc": 0.64, "Land": 0.08, "Hb": 2.54, "Tt": 3.81},
        0.02,
    ),
    (
        "round_ffre",
        {"shape": "round", "profile": "ffre", "is_modified": False, "W": 7.94, "L": 7.94, "Dc": 0.64, "Land": 0.08, "Hb": 3.12, "Tt": 4.4},
        0.02,
    ),
    (
        "round_ffbe",
        {"shape": "round", "profile": "ffbe", "is_modified": False, "W": 7.94, "L": 7.94, "Dc": 0.64, "Land": 0.08, "Hb": 3.12, "Tt": 4.4, "Bev_A": 30.0},
        0.02,
    ),
    # Capsule
    (
        "capsule_concave",
        {"shape": "capsule", "profile": "concave", "is_modified": False, "W": 7.94, "L": 19.05, "Dc": 1.47, "Land": 0.08, "Hb": 2.54, "Tt": 5.48, "Rc_min": 5.882},
        0.02,
    ),
    (
        "capsule_cbe",
        {"shape": "capsule", "profile": "cbe", "is_modified": False, "W": 7.94, "L": 19.05, "Dc": 1.47, "Land": 0.08, "Hb": 2.54, "Tt": 5.48},
        0.02,
    ),
    (
        "capsule_ffre",
        {"shape": "capsule", "profile": "ffre", "is_modified": False, "W": 7.94, "L": 19.05, "Dc": 1.47, "Land": 0.08, "Hb": 2.54, "Tt": 5.48},
        0.06,
    ),
    (
        "capsule_ffbe",
        {"shape": "capsule", "profile": "ffbe", "is_modified": False, "W": 7.94, "L": 19.05, "Dc": 1.47, "Land": 0.08, "Hb": 2.54, "Tt": 5.48, "Bev_A": 30.0},
        0.02,
    ),
    (
        "capsule_modified_concave",
        {"shape": "capsule", "profile": "concave", "is_modified": True, "W": 7.94, "L": 19.05, "Re": 3.818, "Rs": 111.0316, "Dc": 1.47, "Land": 0.08, "Hb": 2.54, "Tt": 5.48, "Rc_min": 5.882},
        0.20,
    ),
    (
        "capsule_modified_cbe",
        {"shape": "capsule", "profile": "cbe", "is_modified": True, "W": 7.94, "L": 19.05, "Re": 3.818, "Rs": 111.0316, "Dc": 1.47, "Land": 0.08, "Hb": 2.54, "Tt": 5.48},
        0.20,
    ),
    # Oval
    (
        "oval_concave",
        {"shape": "oval", "profile": "concave", "is_modified": False, "W": 7.94, "L": 15.56, "Re": 3.05, "Rs": 15.66918, "Dc": 1.42, "Land": 0.08, "Hb": 3.18, "Tt": 6.02, "Rc_min": 6.0382, "Rc_maj": 21.587},
        0.06,
    ),
    (
        "oval_modified_oval",
        {"shape": "oval", "profile": "modified_oval", "is_modified": False, "W": 7.94, "L": 15.56, "Re": 3.05, "Rs": 15.66918, "Dc": 1.42, "Land": 0.08, "Hb": 3.18, "Tt": 6.02},
        0.13,
    ),
    (
        "oval_compound",
        {"shape": "oval", "profile": "compound", "is_modified": False, "W": 7.94, "L": 15.56, "Re": 3.05, "Rs": 15.66918, "Dc": 1.42, "Land": 0.08, "Hb": 3.18, "Tt": 6.02},
        0.10,
    ),
    (
        "oval_cbe",
        {"shape": "oval", "profile": "cbe", "is_modified": False, "W": 7.94, "L": 15.56, "Re": 3.05, "Rs": 15.66918, "Dc": 1.42, "Land": 0.08, "Hb": 3.18, "Tt": 6.02},
        0.13,
    ),
    (
        "oval_ffre",
        {"shape": "oval", "profile": "ffre", "is_modified": False, "W": 7.94, "L": 15.56, "Re": 3.05, "Rs": 15.66918, "Dc": 1.42, "Land": 0.08, "Hb": 3.18, "Tt": 6.02},
        0.13,
    ),
    (
        "oval_ffbe",
        {"shape": "oval", "profile": "ffbe", "is_modified": False, "W": 7.94, "L": 15.56, "Re": 3.05, "Rs": 15.66918, "Dc": 1.42, "Land": 0.08, "Hb": 3.18, "Tt": 6.02, "Bev_A": 30.0},
        0.10,
    ),
]


def _max_rel_err(a, b):
    rels = []
    for k in METRIC_KEYS:
        av = float(a[k])
        bv = float(b[k])
        rels.append(abs(av - bv) / max(1e-9, abs(bv)))
    return max(rels), rels


def test_golden_regression_metrics():
    failures = []
    for name, params, tol in CASES:
        p = _base_params()
        p.update(params)
        _, m_ref = render_from_reference(p)
        m_dom = generate_mesh(p)["metrics"]
        max_rel, rels = _max_rel_err(m_dom, m_ref)
        if max_rel > tol or math.isnan(max_rel):
            failures.append((name, tol, max_rel, rels, m_dom, m_ref))

    if failures:
        lines = ["Golden regression mismatch:"]
        for name, tol, max_rel, rels, m_dom, m_ref in failures:
            lines.append(f"- {name}: max_rel={max_rel:.6f}, tol={tol:.6f}, rels={rels}")
            lines.append(f"  domain={m_dom}")
            lines.append(f"  ref={m_ref}")
        raise AssertionError("\n".join(lines))
