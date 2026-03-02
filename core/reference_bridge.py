import base64
import importlib.util
from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
REF_ROOT = ROOT / "core" / "natoli_forms"

_MODULE_CACHE: Dict[str, object] = {}


def _profile_key(shape: str, profile: str, is_modified: bool) -> str:
    if shape == "round":
        return {
            "concave": "Round/Concave/ConcaveRound.py",
            "compound": "Round/CompoundCup/CompoundCupRound.py",
            "cbe": "Round/ConcaveBevelEdge/ConcaveBevelEdgeRound.py",
            "ffre": "Round/FlatFaceRadiusEdge/FlatFaceRadiusEdgeRound.py",
            "ffbe": "Round/FlatFaceBevelEdge/FlatFaceBevelEdgeRound.py",
        }.get(profile, "Round/Concave/ConcaveRound.py")

    if shape == "capsule":
        if is_modified:
            return {
                "concave": "Capsule/Modifed/Concave/ConcaveModifedCapsule.py",
                "cbe": "Capsule/Modifed/ConcaveBevelEdge/ConcaveBevelEdgeModifedCapsule.py",
            }.get(profile, "Capsule/Modifed/Concave/ConcaveModifedCapsule.py")
        return {
            "concave": "Capsule/Capsule/Concave/ConcaveCapsule.py",
            "cbe": "Capsule/Capsule/ConcaveBevelEdge/ConcaveBevelEdgeCapsule.py",
            "ffre": "Capsule/Capsule/FlatFaceRadiusEdge/FlatFaceRadiusEdgeCapsule.py",
            "ffbe": "Capsule/Capsule/FlatFaceBevelEdge/FlatFaceBevelEdgeCapsule.py",
        }.get(profile, "Capsule/Capsule/Concave/ConcaveCapsule.py")

    if profile == "modified_oval":
        return "Oval/Modifed/ModifedOval.py"
    return {
        "concave": "Oval/Concave/ConcaveOval.py",
        "compound": "Oval/CompoundCup/CompoundCupOval.py",
        "cbe": "Oval/ConcaveBevelEdge/ConcaveBevelEdgeOval.py",
        "ffre": "Oval/FlatFaceRadiusEdge/FlatFaceRadiusEdgeOval.py",
        "ffbe": "Oval/FlatFaceBevelEdge/FlatFaceBevelEdgeOval.py",
    }.get(profile, "Oval/Concave/ConcaveOval.py")


def _load_module(rel_path: str):
    if rel_path in _MODULE_CACHE:
        return _MODULE_CACHE[rel_path]

    file_path = REF_ROOT / rel_path
    if not file_path.exists():
        raise FileNotFoundError(f"Reference script not found: {file_path}")

    # Prevent noisy widget output during import.
    import IPython.display as ipd

    old_display = ipd.display
    old_clear = ipd.clear_output
    old_show = plt.show
    ipd.display = lambda *args, **kwargs: None
    ipd.clear_output = lambda *args, **kwargs: None
    plt.show = lambda *args, **kwargs: None
    try:
        module_name = f"natoli_ref_{len(_MODULE_CACHE)}"
        spec = importlib.util.spec_from_file_location(module_name, str(file_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    finally:
        ipd.display = old_display
        ipd.clear_output = old_clear
        plt.show = old_show

    _MODULE_CACHE[rel_path] = module
    return module


def _set_widget(module, names, value):
    for name in names:
        if hasattr(module, name):
            try:
                getattr(module, name).value = value
                return
            except Exception:
                continue


def _sync_inputs(module, params):
    b_type_map = {
        "none": "None",
        "standard": "Standard",
        "cut_through": "Cut Through",
        "decreasing": "Decreasing",
    }

    _set_widget(module, ["ui_D", "ui_W"], params.get("W"))
    _set_widget(module, ["ui_L"], params.get("L"))
    _set_widget(module, ["ui_Re"], params.get("Re"))
    _set_widget(module, ["ui_Rs"], params.get("Rs"))
    _set_widget(module, ["ui_Dc"], params.get("Dc"))
    _set_widget(module, ["ui_Rc", "ui_Rc_min"], params.get("Rc_min"))
    _set_widget(module, ["ui_Rc_maj"], params.get("Rc_maj"))
    _set_widget(module, ["ui_Land"], params.get("Land"))
    _set_widget(module, ["ui_Hb"], params.get("Hb"))
    _set_widget(module, ["ui_Tt"], params.get("Tt"))
    _set_widget(module, ["ui_Bev_D"], params.get("Bev_D"))
    _set_widget(module, ["ui_Bev_A"], params.get("Bev_A"))
    _set_widget(module, ["ui_R_edge"], params.get("R_edge"))
    _set_widget(module, ["ui_Blend_R"], params.get("Blend_R"))
    _set_widget(module, ["ui_R_maj_maj"], params.get("R_maj_maj"))
    _set_widget(module, ["ui_R_maj_min"], params.get("R_maj_min"))
    _set_widget(module, ["ui_b_type"], b_type_map.get(params.get("b_type", "none"), "None"))
    _set_widget(module, ["ui_b_width"], params.get("b_width", 0.0))
    _set_widget(module, ["ui_b_depth"], params.get("b_depth", 0.0))
    _set_widget(module, ["ui_b_angle"], params.get("b_angle", 90.0))
    _set_widget(module, ["ui_b_Ri"], params.get("b_Ri", 0.06))


def _read_metrics(module) -> Dict[str, float]:
    def val(name):
        return float(getattr(module, name).value) if hasattr(module, name) else 0.0

    return {
        "Die_Hole_SA": round(val("ui_calc_die"), 4),
        "Cup_Volume": round(val("ui_calc_cvol"), 4),
        "Cup_SA": round(val("ui_calc_csa"), 4),
        "Perimeter": round(val("ui_calc_perim"), 4),
        "Tablet_SA": round(val("ui_calc_tsa"), 4),
        "Tablet_Vol": round(val("ui_calc_tvol"), 4),
    }


def render_from_reference(params) -> Tuple[str, Dict[str, float]]:
    rel_path = _profile_key(params.get("shape", "round"), params.get("profile", "concave"), bool(params.get("is_modified", False)))
    module = _load_module(rel_path)
    _sync_inputs(module, params)

    plt.close("all")
    old_show = plt.show
    plt.show = lambda *args, **kwargs: None
    try:
        module.draw_views()
    finally:
        plt.show = old_show

    fig = plt.gcf()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    img_src = f"data:image/png;base64,{base64.b64encode(buf.getbuffer()).decode('ascii')}"
    return img_src, _read_metrics(module)
