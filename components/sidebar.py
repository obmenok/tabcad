from dash import html, dcc
import dash_bootstrap_components as dbc

def make_input(id, label, default_val, step=0.01, min_value=0.01, debounce=False):
    return html.Div(
        dbc.InputGroup([
            dbc.InputGroupText(label, id=f"label-{id}", style={'width': '140px', 'fontSize': '0.9rem'}),
            dbc.Input(id=id, type='number', value=default_val, step=step, min=min_value, debounce=debounce)
        ], className="mb-2"),
        id=f"div-{id}" 
    )

def create_sidebar():
    return html.Div([
        html.H4("Tablet Design", className="text-primary mb-3"),
        
        html.Label("Tablet Shape", className="fw-bold mt-2"),
        dcc.Dropdown(
            id='shape-dropdown',
            options=[
                {'label': 'Round', 'value': 'round'},
                {'label': 'Capsule', 'value': 'capsule'},
                {'label': 'Oval', 'value': 'oval'}
            ],
            value='round', clearable=False, className="mb-2" 
        ),
        
        html.Div(
            dbc.Checklist(options=[{"label": "Modified Shape", "value": True}], value=[], id="modified-switch", switch=True, className="mb-3"),
            id="div-modified-switch"
        ),

        html.Label("Cup Configuration", className="fw-bold"),
        dcc.Dropdown(
            id='profile-dropdown',
            options=[{'label': 'Concave', 'value': 'concave'}, {'label': 'Compound Cup', 'value': 'compound'}],
            value='compound', clearable=False, className="mb-4"
        ),

        html.H6("Dimensions", className="fw-bold text-secondary border-bottom pb-1"),
        make_input('input-w', 'Minor Axis', 8.0), 
        make_input('input-l', 'Major Axis', 18.3),
        make_input('input-re', 'End Radius', 4.6),
        make_input('input-rs', 'Side Radius', 15.0, min_value=0.0),
        
        make_input('input-dc', 'Cup Depth', 0.92),
        # Rc делаем справочными (disabled), как в оригинале!
        html.Div(dbc.InputGroup([dbc.InputGroupText('Cup Radius', id='label-input-rc-min', style={'width': '140px', 'fontSize': '0.9rem'}), dbc.Input(id='input-rc-min', type='number', value=8.8, min=0.01, disabled=True)], className="mb-2"), id="div-input-rc-min"),
        html.Div(dbc.InputGroup([dbc.InputGroupText('Cup Radius Maj', id='label-input-rc-maj', style={'width': '140px', 'fontSize': '0.9rem'}), dbc.Input(id='input-rc-maj', type='number', value=39.8, min=0.01, disabled=True)], className="mb-2"), id="div-input-rc-maj"),
        
        make_input('input-r-maj-maj', 'Major Major Rad.', 88.9),
        make_input('input-r-maj-min', 'Major Minor Rad.', 6.35),
        make_input('input-r-min-maj', 'Minor Major Rad.', 12.7),
        make_input('input-r-min-min', 'Minor Minor Rad.', 3.81),
        make_input('input-bev-d', 'Bevel Depth', 0.51),
        make_input('input-bev-a', 'Bevel Angle', 40.0, step=0.01),
        make_input('input-r-edge', 'Radius Edge', 6.35),
        make_input('input-blend-r', 'Blend Radius', 0.38),
        
        make_input('input-land', 'Land', 0.08),
        make_input('input-hb', 'Belly Band', 2.55),
        make_input('input-tt', 'Tablet Thickness', 4.39), # ТЕПЕРЬ ДОСТУПНО ДЛЯ ВВОДА!
        make_input('input-density', 'Tablet Density', 1.19, step=0.01, min_value=0.01, debounce=True),
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
            dbc.Checklist(
                options=[{"label": "Cruciform", "value": "on"}],
                value=[],
                id="bisect-cruciform",
                switch=True,
                className="mb-2",
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
                className="mb-2",
            ),
            id="div-bisect-double-sided",
            style={"display": "none"},
        ),
        make_input('input-b-width', 'Width', 2.25),
        make_input('input-b-depth', 'Depth', 1.12),
        make_input('input-b-angle', 'Angle', 90.0),
        make_input('input-b-ri', 'Radius Inner', 0.06),

        html.Hr(),
        dbc.Button("Generate Drawing", id="btn-generate", color="primary", className="w-100 mb-3")
    ])
