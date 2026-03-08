from dash import html, dcc
import dash_bootstrap_components as dbc
from core.defaults import BASE_DEFAULTS, PROFILE_DEFAULTS, BISECT_DEFAULTS, SHAPE_SPECIFIC

def make_input(id, label, default_val, step=0.01, min_value=0.01, max_value=None, debounce=True):
    return html.Div(
        dbc.InputGroup([
            dbc.InputGroupText(label, id=f"label-{id}", style={'width': '140px', 'fontSize': '0.85rem'}),
            dbc.Input(id=id, type='number', value=default_val, step=step, min=min_value, max=max_value, debounce=debounce, size="sm")
        ], className="mb-2", size="sm"),
        id=f"div-{id}" 
    )

def create_sidebar():
    return html.Div([
        dcc.Store(id="bisect-edit-open", data=False),
        dcc.Store(id="is-loading-preset", data=False),
        
        html.H4("TabletCAD Pro", className="text-primary mb-3"),
        
        # --- PRESETS UI ---
        html.Div([
            html.Label("Saved Presets", className="fw-bold text-secondary"),
            html.Div([
                html.Div(dbc.Select(
                    id='preset-dropdown', 
                    options=[],
                    size="sm"
                ), style={"flex": "1", "minWidth": "0"}),
                dbc.ButtonGroup([
                    dbc.Button("Load", id="preset-load-btn", color="light", class_name="plotly-toolbar-btn"),
                    dbc.Button("Save", id="preset-save-btn", color="light", class_name="plotly-toolbar-btn"),
                    dbc.Button("Save As", id="preset-save-as-btn", color="light", class_name="plotly-toolbar-btn"),
                    dbc.Button("Del", id="preset-delete-btn", color="light", class_name="plotly-toolbar-btn"),
                ], size="sm", className="ms-1 plotly-toolbar-group")
            ], className="d-flex align-items-center mb-3", style={"height": "40px"}),
        ]),

        # Save As Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Save Preset As")),
            dbc.ModalBody(
                dbc.Input(id="preset-name-input", placeholder="Enter preset name...", type="text")
            ),
            dbc.ModalFooter([
                dbc.Button("Save", id="preset-modal-save-btn", color="success", className="ms-auto"),
                dbc.Button("Cancel", id="preset-modal-cancel-btn", color="secondary")
            ]),
        ], id="preset-save-modal", is_open=False, centered=True),
        # ------------------

        html.H5("Tablet Design", className="text-secondary border-bottom pb-1 mt-2"),
        
        html.Label("Tablet Shape", className="fw-bold mt-2"),
        html.Div(
            dbc.ButtonGroup(
                [
                    dbc.Button("Round", id="shape-round-btn", color="light", class_name="plotly-toolbar-btn active"),
                    dbc.Button("Capsule", id="shape-capsule-btn", color="light", class_name="plotly-toolbar-btn"),
                    dbc.Button("Oval", id="shape-oval-btn", color="light", class_name="plotly-toolbar-btn"),
                ],
                size="sm",
                className="w-100 plotly-toolbar-group",
            ),
            style={"height": "40px", "display": "flex", "alignItems": "center"},
            className="mb-1"
        ),
        dcc.Dropdown(
            id='shape-dropdown',
            options=[
                {'label': 'Round', 'value': 'round'},
                {'label': 'Capsule', 'value': 'capsule'},
                {'label': 'Oval', 'value': 'oval'}
            ],
            value='round', clearable=False, style={'display': 'none'}
        ),
        
        html.Div(
            dbc.Checklist(options=[{"label": "Modified Shape", "value": True}], value=[], id="modified-switch", switch=True, className="mb-3"),
            id="div-modified-switch"
        ),

        html.Label("Cup Configuration", className="fw-bold"),
        dcc.Dropdown(
            id='profile-dropdown',
            options=[{'label': 'Concave', 'value': 'concave'}, {'label': 'Compound Cup', 'value': 'compound'}],
            value='concave', clearable=False, searchable=False, className="mb-4"
        ),

        html.H6("Dimensions", className="fw-bold text-secondary border-bottom pb-1"),
        make_input('input-w', 'Minor Axis', BASE_DEFAULTS["W"]), 
        make_input('input-l', 'Major Axis', BASE_DEFAULTS["L"]),
        make_input('input-re', 'End Radius', SHAPE_SPECIFIC["oval"]["re"]),
        make_input('input-rs', 'Side Radius', SHAPE_SPECIFIC["oval"]["rs"], min_value=0.0),
        
        make_input('input-dc', 'Cup Depth', BASE_DEFAULTS["dc"]),
        # Rc делаем справочными (disabled), как в оригинале!
        html.Div(dbc.InputGroup([dbc.InputGroupText('Cup Radius', id='label-input-rc-min', style={'width': '140px', 'fontSize': '0.85rem'}), dbc.Input(id='input-rc-min', type='number', value=PROFILE_DEFAULTS["concave"]["rc_min"], min=0.01, disabled=True, size="sm", className="form-control-sm")], className="mb-2 input-group-sm", size="sm"), id="div-input-rc-min"),
        html.Div(dbc.InputGroup([dbc.InputGroupText('Cup Radius Maj', id='label-input-rc-maj', style={'width': '140px', 'fontSize': '0.85rem'}), dbc.Input(id='input-rc-maj', type='number', value=PROFILE_DEFAULTS["concave"]["rc_maj"], min=0.01, disabled=True, size="sm", className="form-control-sm")], className="mb-2 input-group-sm", size="sm"), id="div-input-rc-maj"),
        
        make_input('input-r-maj-maj', 'Major Major Rad.', PROFILE_DEFAULTS["compound"]["r_maj_maj"]),
        make_input('input-r-maj-min', 'Major Minor Rad.', PROFILE_DEFAULTS["compound"]["r_maj_min"]),
        make_input('input-r-min-maj', 'Minor Major Rad.', PROFILE_DEFAULTS["compound"]["r_min_maj"]),
        make_input('input-r-min-min', 'Minor Minor Rad.', PROFILE_DEFAULTS["compound"]["r_min_min"]),
        make_input('input-bev-d', 'Bevel Depth', PROFILE_DEFAULTS["cbe"]["bev_d"]),
        make_input('input-bev-a', 'Bevel Angle', PROFILE_DEFAULTS["cbe"]["bev_a"], step=0.01, max_value=60.0),
        make_input('input-r-edge', 'Radius Edge', PROFILE_DEFAULTS["ffre"]["r_edge"]),
        make_input('input-blend-r', 'Blend Radius', PROFILE_DEFAULTS["ffbe"]["blend_r"]),
        
        make_input('input-land', 'Land', BASE_DEFAULTS["land"]),
        make_input('input-hb', 'Belly Band', BASE_DEFAULTS["hb"]),
        make_input('input-tt', 'Tablet Thickness', BASE_DEFAULTS["tt"]), # ТЕПЕРЬ ДОСТУПНО ДЛЯ ВВОДА!
        make_input('input-density', 'Tablet Density', BASE_DEFAULTS["density"], step=0.01, min_value=0.01, debounce=True),
        make_input('input-weight', 'Tablet Weight', None, step=0.01, min_value=0.0, debounce=True),

        html.H6("Bisect Options", className="fw-bold text-secondary border-bottom pb-1 mt-3"),
        dcc.Dropdown(
            id='bisect-type',
            # ВОТ ЗДЕСЬ ВЕРНУЛИ ВСЕ 4 ОПЦИИ РИСКИ
            options=[
                {'label': 'None', 'value': 'none'}, 
                {'label': 'Standard', 'value': 'standard'},
                {'label': 'Cut Through', 'value': 'cut_through'},
                {'label': 'Decreasing', 'value': 'decreasing'}
            ],
            value='standard', clearable=False, className="mb-2"
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            dbc.Checklist(
                                options=[{"label": "Cruciform", "value": "on"}],
                                value=[],
                                id="bisect-cruciform",
                                switch=True,
                                className="mb-0",
                            ),
                            id="div-bisect-cruciform",
                            style={"display": "none"},
                        ),
                        html.Div(
                            dbc.Checklist(
                                options=[{"label": "Double-sided", "value": "on"}],
                                value=[],
                                id="bisect-double-sided",
                                switch=True,
                                className="mb-0",
                            ),
                            id="div-bisect-double-sided",
                            style={"display": "none"},
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center"},
                ),
                dbc.Button(
                    "Edit",
                    id="bisect-edit-btn",
                    outline=True,
                    color="secondary",
                    size="sm",
                    className="bisect-edit-btn",
                ),
            ],
            id="div-bisect-controls-row",
            className="mb-2",
            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
        ),
        make_input('input-b-width', 'Width', BISECT_DEFAULTS["standard"]["width"]),
        make_input('input-b-depth', 'Depth', BISECT_DEFAULTS["standard"]["depth"]),
        make_input('input-b-angle', 'Angle', BISECT_DEFAULTS["standard"]["angle"]),
        make_input('input-b-ri', 'Radius Inner', BISECT_DEFAULTS["standard"]["ri"]),

        html.Hr(),
        dbc.Button("Generate Drawing", id="btn-generate", color="primary", className="w-100 mb-3")
    ])
