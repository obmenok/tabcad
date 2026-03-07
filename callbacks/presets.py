from dash import Input, Output, State, callback, ctx, dash
from core import db

# Список всех ID параметров (State) для сохранения/загрузки
PRESET_KEYS = [
    "shape-dropdown", "profile-dropdown", "modified-switch", 
    "input-w", "input-l", "input-re", "input-rs", 
    "input-dc", "input-rc-min", "input-rc-maj", 
    "input-r-maj-maj", "input-r-maj-min", "input-r-min-maj", "input-r-min-min",
    "input-bev-d", "input-bev-a", "input-r-edge", "input-blend-r", 
    "input-land", "input-hb", "input-tt", "input-density", "input-weight",
    "bisect-type", "bisect-cruciform", "bisect-double-sided",
    "input-b-width", "input-b-depth", "input-b-angle", "input-b-ri"
]

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
    
    # Вспомогательная функция для получения актуального списка опций
    def get_options():
        names = db.get_all_preset_names()
        opts = [{'label': "Select preset...", 'value': '', 'disabled': True}]
        opts.extend([{'label': n, 'value': n} for n in names])
        return opts

    # Если вызов произошел при первоначальной загрузке страницы
    if not trig:
        return dash.no_update, get_options()
        
    if trig == "preset-delete-btn" and current_preset:
        db.delete_preset(current_preset)
        return None, get_options()
        
    # Собираем словарь параметров из интерфейса
    params = dict(zip(PRESET_KEYS, values))
    
    if trig == "preset-modal-save-btn" and new_name:
        # Сохранить как новый
        name = new_name.strip()
        if name:
            db.save_preset(name, params)
            return name, get_options()
            
    if trig == "preset-save-btn" and current_preset:
        # Перезаписать текущий
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
