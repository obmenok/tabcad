from dash import Input, Output, State, callback, ctx, dash
from core import db
from core.preset_naming import build_preset_base_name

# Список всех ID параметров (State) для сохранения/загрузки
PRESET_KEYS = [
    "shape-dropdown", "profile-dropdown", "modified-switch", 
    "input-w", "input-l", "input-re", "input-rs", 
    "input-dc", "input-rc-min", "input-rc-maj", 
    "input-r-maj-maj", "input-r-maj-min", "input-r-min-maj", "input-r-min-min",
    "input-bev-d", "input-bev-a", "input-r-edge", "input-blend-r", 
    "input-land", "input-hb", "input-tt", "input-density", "input-weight", "input-tip-force-steel",
    "bisect-type", "bisect-cruciform", "bisect-double-sided",
    "input-b-width", "input-b-depth", "input-b-angle", "input-b-ri"
]

EMPTY_PRESET_OPTION = {
    "label": "No presets saved",
    "value": "__no_presets__",
    "disabled": True,
}

def _generate_preset_name(shape, profile, is_mod, w, l, tt, b_type, b_cruciform, b_double):
    """???????????????????? ?????? ?????????????? ???? ???????????? ?????????????? ????????????????????, ?? ???????????????????????????? ???????????????????? (-00, -01, etc)."""
    base_name = build_preset_base_name(
        shape, profile, is_mod, w, l, tt, b_type, b_cruciform, b_double
    )

    # ?????????? ???????????????????????? ???????????????? ?? ?????????? ???? ?????????????? ???????????? ?????? ?????????????????????? ???????????????????? ????????????
    existing_names = db.get_preset_names_starting_with(base_name)

    max_suffix = -1
    for name in existing_names:
        # ??????????????????, ?????????? ???? ?????? ???????????? "base_name-XX"
        if name.startswith(f"{base_name}-"):
            suffix_part = name[len(base_name)+1:]
            if suffix_part.isdigit() and len(suffix_part) == 2:
                max_suffix = max(max_suffix, int(suffix_part))

    # ?????????????????? ?????????????????? ?????????? (???????? ???????????????? ??????, ?????????? 00)
    next_suffix = max_suffix + 1
    return f"{base_name}-{next_suffix:02d}"


@callback(
    [Output("preset-save-modal", "is_open"), Output("preset-name-input", "value")],
    [
        Input("preset-save-as-btn", "n_clicks"),
        Input("preset-modal-cancel-btn", "n_clicks"),
        Input("preset-modal-save-btn", "n_clicks"),
    ],
    [
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
    ],
    prevent_initial_call=True
)
def toggle_modal(n_open, n_cancel, n_save, is_open, shape, profile, is_mod, w, l, tt, b_type, b_cruciform, b_double):
    """Управляет открытием окна и генерирует имя по стандартам Natoli."""
    trig = ctx.triggered_id
    
    if trig == "preset-save-as-btn":
        auto_name = _generate_preset_name(shape, profile, is_mod, w, l, tt, b_type, b_cruciform, b_double)
        return True, auto_name
        
    return False, dash.no_update


@callback(
    [
        Output("preset-dropdown", "value", allow_duplicate=True),
        Output("preset-dropdown", "options", allow_duplicate=True)
    ],
    [
        Input("preset-save-btn", "n_clicks"),
        Input("preset-modal-save-btn", "n_clicks"),
        Input("preset-delete-btn", "n_clicks")
    ],
    [
        State("preset-dropdown", "value"),
        State("preset-name-input", "value"),
    ] + [State(k, "value") for k in PRESET_KEYS],
    prevent_initial_call="initial_duplicate"
)
def handle_preset_actions(save_btn, modal_save_btn, delete_btn, current_preset, new_name, *values):
    """Обрабатывает сохранение/удаление пресетов и обновляет список."""
    trig = ctx.triggered_id
    
    def get_options():
        names = db.get_all_preset_names()
        if not names:
            return [EMPTY_PRESET_OPTION]
        return [{'label': n, 'value': n} for n in names]

    if not trig:
        return dash.no_update, get_options()
        
    if trig == "preset-delete-btn" and current_preset:
        db.delete_preset(current_preset)
        return None, get_options()
        
    params = dict(zip(PRESET_KEYS, values))
    
    if trig == "preset-modal-save-btn" and new_name:
        name = new_name.strip()
        if name:
            db.save_preset(name, params)
            return name, get_options()
            
    if trig == "preset-save-btn" and current_preset:
        # Для кнопки "Save" мы перезаписываем текущий пресет.
        # Имя не меняем, чтобы не плодить новые версии (-01, -02) при каждом редактировании.
        db.save_preset(current_preset, params)
        return dash.no_update, dash.no_update
        
    return dash.no_update, dash.no_update



@callback(
    [Output("is-loading-preset", "data", allow_duplicate=True)] +
    [Output(k, "value", allow_duplicate=True) for k in PRESET_KEYS] +
    [
        Output("shape-round-btn", "class_name", allow_duplicate=True),
        Output("shape-capsule-btn", "class_name", allow_duplicate=True),
        Output("shape-oval-btn", "class_name", allow_duplicate=True)
    ],
    Input("preset-load-btn", "n_clicks"),
    State("preset-dropdown", "value"),
    prevent_initial_call=True
)
def load_preset_to_ui(n_clicks, preset_name):
    """Загружает значения из базы данных в UI при нажатии Load."""
    if not preset_name:
        return [dash.no_update] * (len(PRESET_KEYS) + 4)
        
    params = db.load_preset(preset_name)
    if not params:
        return [dash.no_update] * (len(PRESET_KEYS) + 4)
    
    # Формируем список значений для Output в том же порядке, что и PRESET_KEYS
    # Устанавливаем is_loading_preset = True
    outputs = [True] 
    
    loaded_shape = None
    for key in PRESET_KEYS:
        # Если в старом пресете не было какого-то ключа (например, добавили новый), не обновляем его
        val = params.get(key, dash.no_update)
        if key == "shape-dropdown" and val != dash.no_update:
            loaded_shape = val
        outputs.append(val)
        
    # Обновляем классы кнопок форм
    def get_class(shape):
        base = "plotly-toolbar-btn"
        if loaded_shape == shape:
            return f"{base} active"
        return base

    outputs.extend([
        get_class("round") if loaded_shape else dash.no_update,
        get_class("capsule") if loaded_shape else dash.no_update,
        get_class("oval") if loaded_shape else dash.no_update,
    ])
        
    return outputs


@callback(
    Output("is-loading-preset", "data", allow_duplicate=True),
    Input("is-loading-preset", "data"),
    prevent_initial_call=True
)
def reset_loading_flag(is_loading):
    """Сбрасывает флаг загрузки после того, как все компоненты обновились."""
    if is_loading is True:
        return False
    return dash.no_update
