import pandas as pd
import dash
from dash import Input, Output, State, callback


def _load_constraints():
    try:
        df = pd.read_csv("constraints.csv")
        return df.to_dict("records")
    except Exception:
        return []


def _ui_state_for(field, shape, profile, is_modified):
    if shape == "round":
        if field == "Diameter (Round)":
            return "Editable"
        if field in ("Minor Axis (W)", "Major Axis (L)", "End Radius (Re)", "Side Radius (Rs)"):
            return "Hidden"
    else:
        if field == "Diameter (Round)":
            return "Hidden"

    if field == "Minor Axis (W)":
        return "Editable" if shape in ("capsule", "oval") else "Hidden"
    if field == "Major Axis (L)":
        return "Editable" if shape in ("capsule", "oval") else "Hidden"

    if field in ("End Radius (Re)", "Side Radius (Rs)"):
        if shape == "round":
            return "Hidden"
        if shape == "capsule" and not is_modified:
            return "Locked"
        return "Editable"

    if field == "Cup Radius (Rc Min)":
        if shape == "oval":
            return "Locked"
        if shape in ("round", "capsule") and profile in ("concave", "cbe"):
            return "Editable"
        return "Locked"

    if field == "Cup Radius (Rc Maj)":
        if shape == "oval":
            return "Editable" if profile == "cbe" else "Locked"
        return "Hidden"

    if field in ("Major Major Radius", "Major Minor Radius"):
        if profile in ("compound", "modified_oval"):
            return "Editable"
        return "Hidden"

    if field in ("Minor Major Radius", "Minor Minor Radius"):
        if profile == "compound":
            return "Editable"
        return "Hidden"

    if field == "Bevel Depth":
        return "Editable" if profile == "cbe" else "Hidden"
    if field == "Bevel Angle":
        return "Editable" if profile in ("cbe", "ffbe") else "Hidden"
    if field == "Radius Edge":
        return "Editable" if profile == "ffre" else "Hidden"
    if field == "Blend Radius":
        return "Editable" if profile == "ffbe" else "Hidden"

    if field in ("Land", "Belly Band (Hb)", "Tablet Thickness (Tt)", "Tablet Density", "Tablet Weight", "Cup Depth (Dc)"):
        return "Editable"

    return "Varies"


def _allow_field(field):
    if field.startswith("Bisect"):
        return False
    if field in ("Depth (b_depth)", "Width (b_width)", "Angle (b_angle)", "Radius Inner (b_ri)"):
        return False
    return True


@callback(
    Output("constraints-data", "data"),
    [Input("constraints-open-btn", "n_clicks")],
    prevent_initial_call=True,
)
def load_constraints_data(_n_clicks):
    return _load_constraints()


@callback(
    Output("constraints-modal", "is_open"),
    [Input("constraints-open-btn", "n_clicks"), Input("constraints-close-btn", "n_clicks")],
    [State("constraints-modal", "is_open")],
)
def toggle_constraints_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open


@callback(
    [Output("constraints-profile", "options"), Output("constraints-profile", "value")],
    [Input("constraints-shape", "value")],
    [State("constraints-profile", "value")],
)
def update_constraints_profile_options(shape, current):
    base = [{"label": "All Profiles", "value": "all"}]
    if shape == "round":
        options = base + [
            {"label": "Concave", "value": "concave"},
            {"label": "Compound Cup", "value": "compound"},
            {"label": "Concave Bevel Edge", "value": "cbe"},
            {"label": "Flat Face Radius Edge", "value": "ffre"},
            {"label": "Flat Face Bevel Edge", "value": "ffbe"},
        ]
    elif shape == "capsule":
        options = base + [
            {"label": "Concave", "value": "concave"},
            {"label": "Concave Bevel Edge", "value": "cbe"},
            {"label": "Flat Face Radius Edge", "value": "ffre"},
            {"label": "Flat Face Bevel Edge", "value": "ffbe"},
        ]
    elif shape == "oval":
        options = base + [
            {"label": "Concave", "value": "concave"},
            {"label": "Modified Oval", "value": "modified_oval"},
            {"label": "Compound Cup", "value": "compound"},
            {"label": "Concave Bevel Edge", "value": "cbe"},
            {"label": "Flat Face Radius Edge", "value": "ffre"},
            {"label": "Flat Face Bevel Edge", "value": "ffbe"},
        ]
    else:
        options = base + [
            {"label": "Concave", "value": "concave"},
            {"label": "Modified Oval", "value": "modified_oval"},
            {"label": "Compound Cup", "value": "compound"},
            {"label": "Concave Bevel Edge", "value": "cbe"},
            {"label": "Flat Face Radius Edge", "value": "ffre"},
            {"label": "Flat Face Bevel Edge", "value": "ffbe"},
        ]
    available = {o["value"] for o in options}
    value = current if current in available else "concave"
    return options, value


@callback(
    Output("constraints-modified-wrap", "style"),
    [Input("constraints-shape", "value")],
)
def toggle_constraints_modified(shape):
    if shape == "capsule":
        return {"display": "block"}
    return {"display": "none"}


@callback(
    Output("constraints-table", "data"),
    [
        Input("constraints-data", "data"),
        Input("constraints-shape", "value"),
        Input("constraints-profile", "value"),
        Input("constraints-modified", "value"),
    ],
)
def filter_constraints_table(rows, shape, profile, modified_value):
    if not rows:
        return []
    shape = shape or "all"
    profile = profile or "all"
    is_modified = bool(modified_value)
    filtered = []
    for row in rows:
        r_shape = str(row.get("Shape", "all")).lower()
        r_profile = str(row.get("Profile", "all")).lower()
        r_mod = str(row.get("Modified", "no")).lower()
        shape_ok = (r_shape == shape)
        profile_ok = (r_profile == profile)
        mod_ok = (r_mod == ("yes" if is_modified else "no"))
        if not (shape_ok and profile_ok and mod_ok):
            continue
        filtered.append(row)
    return filtered
