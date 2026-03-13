from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from core.defaults import BASE_DEFAULTS, PROFILE_DEFAULTS, BISECT_DEFAULTS, SHAPE_SPECIFIC

def make_input(id, label, default_val, step=0.01, min_value=0.01, max_value=None, debounce=True, disabled=False):
    return html.Div(
        dbc.InputGroup([
            dbc.InputGroupText(label, id=f"label-{id}", className="tablet-input-label", style={'width': '140px'}),
            dbc.Input(
                id=id,
                type='number',
                value=default_val,
                step=step,
                min=min_value,
                max=max_value,
                debounce=debounce,
                disabled=disabled,
                size="sm",
                className="tablet-input-control",
            )
        ], className="mb-2 input-group-sm", size="sm"),
        id=f"div-{id}" 
    )

def create_sidebar():
    return html.Div([
        dcc.Store(id="bisect-edit-open", data=False),
        dcc.Store(id="is-loading-preset", data=False),
        dcc.Store(id="constraints-data", data=[]),
        
        html.H4("TabletCAD Pro", className="text-primary mb-3"),
        
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Constraints Inspector")),
                dbc.ModalBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="constraints-shape",
                                        options=[
                                            {"label": "All Shapes", "value": "all"},
                                            {"label": "Round", "value": "round"},
                                            {"label": "Capsule", "value": "capsule"},
                                            {"label": "Oval", "value": "oval"},
                                        ],
                                        value="round",
                                        clearable=False,
                                        searchable=False,
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="constraints-profile",
                                        options=[
                                            {"label": "All Profiles", "value": "all"},
                                            {"label": "Concave", "value": "concave"},
                                            {"label": "Compound Cup", "value": "compound"},
                                            {"label": "Concave Bevel Edge", "value": "cbe"},
                                            {"label": "Flat Face Radius Edge", "value": "ffre"},
                                            {"label": "Flat Face Bevel Edge", "value": "ffbe"},
                                            {"label": "Modified Oval", "value": "modified_oval"},
                                        ],
                                        value="concave",
                                        clearable=False,
                                        searchable=False,
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                    dbc.Checklist(
                                        options=[{"label": "Modified", "value": True}],
                                        value=[],
                                        id="constraints-modified",
                                        switch=True,
                                        className="mb-0",
                                    ),
                                    id="constraints-modified-wrap",
                                    width=6,
                                ),
                            ],
                            className="g-2 mb-3",
                        ),
                        dash_table.DataTable(
                            id="constraints-table",
                            columns=[
                                {"name": "Field", "id": "Field"},
                                {"name": "Default Value", "id": "Default Value"},
                                {"name": "UI State", "id": "UI State"},
                                {"name": "Min", "id": "Min"},
                                {"name": "Max", "id": "Max"},
                                {"name": "Affected Fields", "id": "Affected Fields"},
                                {"name": "Influenced By", "id": "Influenced By"},
                                {"name": "Notes", "id": "Notes"},
                            ],
                            data=[],
                            page_size=12,
                            sort_action="native",
                            style_table={"maxHeight": "55vh", "overflowY": "auto"},
                            style_cell={
                                "fontSize": "0.85rem",
                                "padding": "6px",
                                "whiteSpace": "normal",
                                "height": "auto",
                                "textAlign": "left",
                            },
                            style_header={
                                "fontWeight": "600",
                                "backgroundColor": "#f6f7f9",
                            },
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="constraints-close-btn", color="secondary")
                ),
            ],
            id="constraints-modal",
            is_open=False,
            size="xl",
            centered=True,
        ),

        
        html.Label("Tablet Shape", className="fw-bold m-0"),
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
            [
                html.Label("Cup Configuration", className="fw-bold m-0"),
                html.Div(
                    dbc.Checklist(
                        options=[{"label": "Modified Shape", "value": True}],
                        value=[],
                        id="modified-switch",
                        switch=True,
                        className="mb-0",
                    ),
                    id="div-modified-switch",
                ),
            ],
            className="mb-0 mt-2",
            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
        ),
        html.Div(
            [
                dbc.ButtonGroup(
                    [
                        dbc.Button(
                            "CON",
                            id="profile-btn-con",
                            color="light",
                            class_name="plotly-toolbar-btn cup-config-btn",
                            size="sm",
                            title="Concave",
                        ),
                        dbc.Button(
                            "COM",
                            id="profile-btn-com",
                            color="light",
                            class_name="plotly-toolbar-btn cup-config-btn",
                            size="sm",
                            title="Compound Cup",
                        ),
                        dbc.Button(
                            "CBE",
                            id="profile-btn-cbe",
                            color="light",
                            class_name="plotly-toolbar-btn cup-config-btn",
                            size="sm",
                            title="Concave Bevel Edge",
                        ),
                        dbc.Button(
                            "FFRE",
                            id="profile-btn-ffre",
                            color="light",
                            class_name="plotly-toolbar-btn cup-config-btn",
                            size="sm",
                            title="Flat Face Radius Edge",
                        ),
                        dbc.Button(
                            "FFBE",
                            id="profile-btn-ffbe",
                            color="light",
                            class_name="plotly-toolbar-btn cup-config-btn",
                            size="sm",
                            title="Flat Face Bevel Edge",
                        ),
                        dbc.Button(
                            "MOD",
                            id="profile-btn-mod",
                            color="light",
                            class_name="plotly-toolbar-btn cup-config-btn",
                            size="sm",
                            title="Modified Oval",
                        ),
                    ],
                    size="sm",
                    className="w-100 plotly-toolbar-group cup-config-group",
                ),
            ],
            className="mb-1",
            style={"height": "40px", "display": "flex", "alignItems": "center"},
        ),
        dcc.Dropdown(
            id='profile-dropdown',
            options=[{'label': 'Concave', 'value': 'concave'}, {'label': 'Compound Cup', 'value': 'compound'}],
            value='concave',
            clearable=False,
            searchable=False,
            style={'display': 'none'},
        ),

        html.Div(
            [
                html.H6("Dimensions", className="fw-bold text-secondary mb-0"),
                dbc.Button(
                    "Constraints",
                    id="constraints-open-btn",
                    outline=True,
                    color="secondary",
                    size="sm",
                    className="bisect-edit-btn",
                ),
            ],
            className="border-bottom pb-1 mb-2 mt-2",
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
        ),
        make_input('input-w', 'Minor Axis', BASE_DEFAULTS["W"]), 
        make_input('input-l', 'Major Axis', BASE_DEFAULTS["L"]),
        make_input('input-re', 'End Radius', SHAPE_SPECIFIC["oval"]["re"]),
        make_input('input-rs', 'Side Radius', SHAPE_SPECIFIC["oval"]["rs"], min_value=0.0),
        
        make_input('input-dc', 'Cup Depth', BASE_DEFAULTS["dc"]),
        # Rc делаем справочными (disabled), как в оригинале!
        make_input('input-rc-min', 'Cup Radius', PROFILE_DEFAULTS["concave"]["rc_min"], disabled=True),
        make_input('input-rc-maj', 'Cup Radius Maj', PROFILE_DEFAULTS["concave"]["rc_maj"], disabled=True),
        
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
