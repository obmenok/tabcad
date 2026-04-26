import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from core.defaults import BASE_DEFAULTS, PROFILE_DEFAULTS, BISECT_DEFAULTS, SHAPE_SPECIFIC, DEFAULT_APP_SETTINGS
from components.settings_modal import create_settings_modal

def make_input(id, label, default_val, step=0.01, min_value=0.01, max_value=None, debounce=True, disabled=False, visible=True):
    step_value = "any" if disabled else step
    style = {"display": "block"} if visible else {"display": "none"}
    return html.Div(
        dbc.InputGroup([
            dbc.InputGroupText(label, id=f"label-{id}", className="tablet-input-label", style={'width': '70%'}),
            dbc.Input(
                id=id,
                type='number',
                value=default_val,
                step=step_value,
                min=None,
                max=None,
                debounce=debounce,
                disabled=disabled,
                size="sm",
                className="tablet-input-control",
                inputMode="decimal",
            )
        ], className="mb-2 input-group-sm", size="sm"),
        id=f"div-{id}",
        style=style
    )

def create_sidebar():
    return html.Div([
        dcc.Store(id="lang-store", storage_type="local", data="en"),
        dcc.Store(id="app-settings-store", storage_type="local", data=DEFAULT_APP_SETTINGS),
        dcc.Store(id="bisect-edit-open", data=False),
        dcc.Store(id="is-loading-preset", data=False),
        dcc.Store(id="constraints-data", data=[]),

        dbc.Row(
            [
                dbc.Col(html.H4("TabCAD", className="text-primary mb-0 fw-bold"), width="auto"),
                dbc.Col(
                    dbc.ButtonGroup(
                        [
                            dbc.Button("EN", id="btn-lang-en", color="primary", size="sm", style={"padding": "2px 6px", "fontSize": "10px"}),
                            dbc.Button("RU", id="btn-lang-ru", color="outline-primary", size="sm", style={"padding": "2px 6px", "fontSize": "10px"}),
                            dbc.Button("CN", id="btn-lang-cn", color="outline-primary", size="sm", style={"padding": "2px 6px", "fontSize": "10px"}),
                        ],
                    ),
                    width="auto",
                    className="ms-auto",
                ),
                dbc.Col(
                    dbc.Button(
                        html.Span(className="apollo-icon av-i-settings", style={"fontSize": "14px"}),
                        id="btn-open-settings",
                        outline=True,
                        color="secondary",
                        size="sm",
                        className="outline-soft-btn",
                        title="Settings",
                    ),
                    width="auto",
                    className="ps-1",
                ),
            ],
            className="mb-3 align-items-center g-0",
        ),
        
        create_settings_modal(),

        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("Constraints Inspector", id="modal-title", style={"fontSize": "16px", "fontWeight": 600}),
                    className="preset-modal-header"
                ),
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
                    ],
                    style={"paddingTop": 0}
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", 
                        id="constraints-close-btn", 
                        outline=True,
                        color="secondary",
                        className="outline-soft-btn preset-modal-btn"
                    ),
                    style={"justifyContent": "flex-end", "borderTop": "none", "gap": "8px", "paddingTop": 0}
                ),
            ],
            id="constraints-modal",
            is_open=False,
            size="xl",
            centered=True,
            className="preset-modal",
        ),


        html.Label("Tablet Shape", id="label-shape-title", className="fw-bold mt-2 mb-1"),
        dbc.ButtonGroup(
            [
                dbc.Button("Round", id="shape-round-btn", color="light", class_name="plotly-toolbar-btn active"),
                dbc.Button("Capsule", id="shape-capsule-btn", color="light", class_name="plotly-toolbar-btn"),
                dbc.Button("Oval", id="shape-oval-btn", color="light", class_name="plotly-toolbar-btn"),
            ],
            size="sm",
            className="plotly-toolbar-group segmented-btn-group tablet-shape-group mb-2",
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
                html.Label("Cup Configuration", id="label-cup-title", className="fw-bold m-0 mb-1"),
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
            className="mb-1 mt-2",
            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
        ),
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
            className="plotly-toolbar-group cup-config-group segmented-btn-group mb-2",
        ),
        dcc.Dropdown(
            id='profile-dropdown',
            options=[{'label': 'Concave', 'value': 'concave'}, {'label': 'Compound Cup', 'value': 'compound'}],
            value='concave',
            clearable=False,
            searchable=False,
            className="small-dropdown cup-config-dropdown mb-2",
        ),

        html.Label("Scoring Options", id="label-scoring-title", className="fw-bold mb-1", style={"marginTop": "4px"}),
        dbc.ButtonGroup(
            [
                dbc.Button("None", id="bisect-btn-none", color="light", class_name="plotly-toolbar-btn", title="None"),
                dbc.Button("Std", id="bisect-btn-standard", color="light", class_name="plotly-toolbar-btn", title="Standard"),
                dbc.Button("Cut", id="bisect-btn-cut", color="light", class_name="plotly-toolbar-btn", title="Cut Through"),
                dbc.Button("Decr", id="bisect-btn-dec", color="light", class_name="plotly-toolbar-btn", title="Decreasing"),
            ],
            size="sm",
            className="plotly-toolbar-group segmented-btn-group bisect-type-group mb-2",
        ),
        dcc.Dropdown(
            id='bisect-type',
            options=[
                {'label': 'None', 'value': 'none'},
                {'label': 'Standard', 'value': 'standard'},
                {'label': 'Cut Through', 'value': 'cut_through'},
                {'label': 'Decreasing', 'value': 'decreasing'}
            ],
            value='standard',
            clearable=False,
            searchable=False,
            className="small-dropdown scoring-type-dropdown mb-2",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            dbc.Checklist(
                                options=[{"label": "Cross-scored", "value": "on"}],
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
                    className="outline-soft-btn",
                ),
            ],
            id="div-bisect-controls-row",
            className="mb-2",
            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
        ),
        make_input('input-b-width', 'Width, mm', BISECT_DEFAULTS["standard"]["width"], visible=False),
        make_input('input-b-depth', 'Depth, mm', BISECT_DEFAULTS["standard"]["depth"], visible=False),
        make_input('input-b-angle', 'Angle, °', BISECT_DEFAULTS["standard"]["angle"], step=1.0, visible=False),
        make_input('input-b-ri', 'Radius Inner, mm', BISECT_DEFAULTS["standard"]["ri"], visible=False),

        html.Div(
            [
                html.Label("Dimensions", id="label-dim-title", className="fw-bold mb-0"),
                dbc.Button(
                    "Constraints",
                    id="constraints-open-btn",
                    outline=True,
                    color="secondary",
                    size="sm",
                    className="outline-soft-btn",
                ),
            ],
            className="mb-2 mt-2",
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
        ),
        make_input('input-w', 'Minor Axis, mm', BASE_DEFAULTS["W"], max_value=25.0),
        make_input('input-l', 'Major Axis, mm', BASE_DEFAULTS["L"], visible=False, max_value=25.0),
        make_input('input-re', 'End Radius, mm', SHAPE_SPECIFIC["oval"]["re"], visible=False),
        make_input('input-rs', 'Side Radius, mm', SHAPE_SPECIFIC["oval"]["rs"], min_value=0.0, visible=False),

        make_input('input-dc', 'Cup Depth, mm', BASE_DEFAULTS["dc"]),
        make_input('input-rc-min', 'Cup Radius, mm', PROFILE_DEFAULTS["concave"]["rc_min"], disabled=True),
        make_input('input-rc-maj', 'Cup Radius Major, mm', PROFILE_DEFAULTS["concave"]["rc_maj"], disabled=True, visible=False),

        make_input('input-r-maj-maj', 'Major Major Radius, mm', PROFILE_DEFAULTS["compound"]["r_maj_maj"], visible=False),
        make_input('input-r-maj-min', 'Major Minor Radius, mm', PROFILE_DEFAULTS["compound"]["r_maj_min"], visible=False),
        make_input('input-r-min-maj', 'Minor Major Radius, mm', PROFILE_DEFAULTS["compound"]["r_min_maj"], visible=False),
        make_input('input-r-min-min', 'Minor Minor Radius, mm', PROFILE_DEFAULTS["compound"]["r_min_min"], visible=False),
        make_input('input-bev-d', 'Bevel Depth, mm', PROFILE_DEFAULTS["cbe"]["bev_d"], visible=False),
        make_input('input-bev-a', 'Bevel Angle, °', PROFILE_DEFAULTS["cbe"]["bev_a"], step=1.0, max_value=60.0, visible=False),
        make_input('input-r-edge', 'Radius Edge, mm', PROFILE_DEFAULTS["ffre"]["r_edge"], visible=False),
        make_input('input-blend-r', 'Blend Radius, mm', PROFILE_DEFAULTS["ffbe"]["blend_r"], visible=False),

        make_input('input-land', 'Land, mm', BASE_DEFAULTS["land"]),
        make_input('input-hb', 'Belly Band, mm', BASE_DEFAULTS["hb"]),
        make_input('input-tt', 'Tablet Thickness, mm', BASE_DEFAULTS["tt"]), 


        html.Hr(),
        dbc.Button("Generate Drawing", id="btn-generate", color="primary", className="w-100 mb-2"),
        dbc.Button("PDF Export", id="export-pdf-btn", color="success", className="w-100 mb-3"),
        dcc.Download(id="download-pdf")
    ], id="sidebar-container", style={"opacity": "0", "transition": "opacity 0.1s", "overflowX": "hidden"})
