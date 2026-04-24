def _fmt_num(val):
    if val is None:
        return ""
    if float(val).is_integer():
        return f"{int(round(float(val)))}"
    return f"{val:.1f}".replace(".", ",")


def build_preset_base_name(shape, profile, is_mod, w, l, tt, b_type, b_cruciform, b_double):
    dim_str = _fmt_num(w) if shape == "round" else f"{_fmt_num(w)}x{_fmt_num(l)}"
    tt_str = _fmt_num(tt)

    form_code = ""
    is_m = bool(is_mod)
    if shape == "round":
        mapping = {
            "concave": "R-CON",
            "compound": "R-COM",
            "cbe": "R-CBE",
            "ffre": "R-FRE",
            "ffbe": "R-FBE",
        }
        form_code = mapping.get(profile, "")
    elif shape == "oval":
        mapping = {
            "concave": "O-CON",
            "modified_oval": "O-MOD",
            "compound": "O-COM",
            "cbe": "O-CBE",
            "ffre": "O-FRE",
            "ffbe": "O-FBE",
        }
        form_code = mapping.get(profile, "")
    elif shape == "capsule":
        if is_m:
            mapping = {
                "concave": "CM-CON",
                "cbe": "CM-CBE",
            }
        else:
            mapping = {
                "concave": "C-CON",
                "cbe": "C-CBE",
                "ffre": "C-FRE",
                "ffbe": "C-FBE",
            }
        form_code = mapping.get(profile, "")

    name_parts = [f"TAB-{dim_str}-{tt_str}-{form_code}"]

    if b_type and b_type != "none":
        b_map = {"standard": "S", "cut_through": "C", "decreasing": "D"}
        name_parts.append(b_map.get(b_type, ""))

        if shape == "round" and bool(b_cruciform):
            name_parts.append("Q")
        elif shape in ("capsule", "oval") and bool(b_double):
            name_parts.append("D")

    return "-".join(filter(bool, name_parts))
