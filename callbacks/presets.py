from dash import Input, Output, State, callback, ctx, dash

from core import db
from core.preset_naming import build_preset_base_name

PRESET_KEYS = [
    "shape-dropdown", "profile-dropdown", "modified-switch",
    "input-w", "input-l", "input-re", "input-rs",
    "input-dc", "input-rc-min", "input-rc-maj",
    "input-r-maj-maj", "input-r-maj-min", "input-r-min-maj", "input-r-min-min",
    "input-bev-d", "input-bev-a", "input-r-edge", "input-blend-r",
    "input-land", "input-hb", "input-tt", "input-density", "input-weight",
    "input-tip-force-steel",
    "bisect-type", "bisect-cruciform", "bisect-double-sided",
    "input-b-width", "input-b-depth", "input-b-angle", "input-b-ri",
]

EMPTY_PRESET_OPTION = {
    "label": "No presets saved",
    "value": "__no_presets__",
    "disabled": True,
}

NO_USER_OPTION = {
    "label": "Sign in to use presets",
    "value": "__no_user__",
    "disabled": True,
}


def _resolve_user_id(token):
    return db.register_or_get_user(token)


def _get_options(user_id):
    if not user_id:
        return [NO_USER_OPTION]
    names = db.get_all_preset_names(user_id)
    if not names:
        return [EMPTY_PRESET_OPTION]
    return [{"label": name, "value": name} for name in names]


def _usage_text(user_id, warning=None):
    if not user_id:
        return "Sign in to save and load presets."
    count = db.count_presets(user_id)
    limit = db.get_preset_limit(user_id)
    prefix = f"{count} / {limit} presets used"
    return f"{prefix}. {warning}" if warning else prefix


def _is_real_preset_name(name):
    return bool(name) and not str(name).startswith("__")


def _generate_preset_name(user_id, shape, profile, is_mod, w, l, tt, b_type, b_cruciform, b_double):
    base_name = build_preset_base_name(
        shape, profile, is_mod, w, l, tt, b_type, b_cruciform, b_double
    )
    existing_names = db.get_preset_names_starting_with(user_id, base_name)

    max_suffix = -1
    for name in existing_names:
        if name.startswith(f"{base_name}-"):
            suffix_part = name[len(base_name) + 1:]
            if suffix_part.isdigit() and len(suffix_part) == 2:
                max_suffix = max(max_suffix, int(suffix_part))

    return f"{base_name}-{max_suffix + 1:02d}"


@callback(
    Output("preset-save-modal", "is_open"),
    Output("preset-name-input", "value"),
    Input("preset-save-as-btn", "n_clicks"),
    Input("preset-modal-cancel-btn", "n_clicks"),
    Input("preset-modal-save-btn", "n_clicks"),
    State("preset-save-modal", "is_open"),
    State("shape-dropdown", "value"),
    State("profile-dropdown", "value"),
    State("modified-switch", "value"),
    State("input-w", "value"),
    State("input-l", "value"),
    State("input-tt", "value"),
    State("bisect-type", "value"),
    State("bisect-cruciform", "value"),
    State("bisect-double-sided", "value"),
    State("user-token-store", "data"),
    prevent_initial_call=True,
)
def toggle_modal(
    n_open,
    n_cancel,
    n_save,
    is_open,
    shape,
    profile,
    is_mod,
    w,
    l,
    tt,
    b_type,
    b_cruciform,
    b_double,
    user_token,
):
    trig = ctx.triggered_id
    if trig == "preset-save-as-btn":
        user_id = _resolve_user_id(user_token)
        if not user_id:
            return False, dash.no_update
        auto_name = _generate_preset_name(
            user_id, shape, profile, is_mod, w, l, tt, b_type, b_cruciform, b_double
        )
        return True, auto_name

    return False, dash.no_update


@callback(
    Output("preset-dropdown", "value", allow_duplicate=True),
    Output("preset-dropdown", "options", allow_duplicate=True),
    Output("preset-limit-msg", "children", allow_duplicate=True),
    Input("preset-save-btn", "n_clicks"),
    Input("preset-modal-save-btn", "n_clicks"),
    Input("preset-delete-btn", "n_clicks"),
    State("preset-dropdown", "value"),
    State("preset-name-input", "value"),
    State("user-token-store", "data"),
    *[State(key, "value") for key in PRESET_KEYS],
    prevent_initial_call="initial_duplicate",
)
def handle_preset_actions(
    save_btn,
    modal_save_btn,
    delete_btn,
    current_preset,
    new_name,
    user_token,
    *values,
):
    trig = ctx.triggered_id
    user_id = _resolve_user_id(user_token)
    if not trig or not user_id:
        return dash.no_update, _get_options(user_id), _usage_text(user_id)

    if trig == "preset-delete-btn" and _is_real_preset_name(current_preset):
        db.delete_preset(user_id, current_preset)
        return None, _get_options(user_id), _usage_text(user_id)

    params = dict(zip(PRESET_KEYS, values))

    if trig == "preset-modal-save-btn" and new_name:
        name = new_name.strip()[:80]
        if name:
            is_new_preset = not db.preset_exists(user_id, name)
            if is_new_preset and db.count_presets(user_id) >= db.get_preset_limit(user_id):
                warning = "Preset limit reached."
                return dash.no_update, _get_options(user_id), _usage_text(user_id, warning)
            db.save_preset(user_id, name, params)
            return name, _get_options(user_id), _usage_text(user_id)

    if trig == "preset-save-btn" and _is_real_preset_name(current_preset):
        db.save_preset(user_id, current_preset, params)
        return dash.no_update, dash.no_update, _usage_text(user_id)

    return dash.no_update, dash.no_update, _usage_text(user_id)


@callback(
    [Output("is-loading-preset", "data", allow_duplicate=True)]
    + [Output(key, "value", allow_duplicate=True) for key in PRESET_KEYS]
    + [
        Output("shape-round-btn", "class_name", allow_duplicate=True),
        Output("shape-capsule-btn", "class_name", allow_duplicate=True),
        Output("shape-oval-btn", "class_name", allow_duplicate=True),
    ],
    Input("preset-load-btn", "n_clicks"),
    State("preset-dropdown", "value"),
    State("user-token-store", "data"),
    prevent_initial_call=True,
)
def load_preset_to_ui(n_clicks, preset_name, user_token):
    no_update_list = [dash.no_update] * (len(PRESET_KEYS) + 4)
    user_id = _resolve_user_id(user_token)
    if not _is_real_preset_name(preset_name) or not user_id:
        return no_update_list

    params = db.load_preset(user_id, preset_name)
    if not params:
        return no_update_list

    outputs = [True]
    loaded_shape = None
    for key in PRESET_KEYS:
        val = params.get(key, dash.no_update)
        if key == "shape-dropdown" and val != dash.no_update:
            loaded_shape = val
        outputs.append(val)

    def get_class(shape):
        base = "plotly-toolbar-btn"
        return f"{base} active" if loaded_shape == shape else base

    outputs.extend([
        get_class("round") if loaded_shape else dash.no_update,
        get_class("capsule") if loaded_shape else dash.no_update,
        get_class("oval") if loaded_shape else dash.no_update,
    ])
    return outputs


@callback(
    Output("preset-dropdown", "options"),
    Output("preset-dropdown", "value"),
    Output("preset-limit-msg", "children"),
    Input("user-id-store", "data"),
    prevent_initial_call=False,
)
def refresh_presets_on_login(user_id):
    return _get_options(user_id), None, _usage_text(user_id)


@callback(
    Output("is-loading-preset", "data", allow_duplicate=True),
    Input("is-loading-preset", "data"),
    prevent_initial_call=True,
)
def reset_loading_flag(is_loading):
    if is_loading is True:
        return False
    return dash.no_update
