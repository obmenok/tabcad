import dash
import dash_bootstrap_components as dbc
from components.sidebar import create_sidebar
from components.viewer import create_model_panel, create_info_panel


# Инициализация приложения (LUMEN - чистая светлая тема, похожая на оригинал)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUMEN], suppress_callback_exceptions=True)
app.title = "TabletCAD Pro"
server = app.server

# Собираем Layout из компонентов
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    create_sidebar(),
                    id="sidebar-container",
                    xs=12,
                    lg=3,
                    className="app-col-left bg-light border-end",
                    style={"height": "100vh", "overflowY": "auto", "overflowX": "hidden", "padding": "20px 10px"},
                ),
                dbc.Col(
                    create_model_panel(),
                    xs=12,
                    lg=6,
                    className="app-col-center bg-white",
                    style={"height": "100vh", "padding": "20px 10px", "minHeight": 0},
                ),
                dbc.Col(
                    create_info_panel(),
                    xs=12,
                    lg=3,
                    className="app-col-right bg-white",
                    style={"height": "100vh", "overflowY": "auto", "overflowX": "hidden", "padding": "20px 10px"},
                ),
            ],
            className="g-0 app-main-row",
        )
    ],
    fluid=True,
    className="g-0",
    style={"overflowX": "hidden"},
)

# Импортируем коллбеки, чтобы они зарегистрировались в app
from callbacks import ui_updater
from callbacks import graph_updater
from callbacks import plotly_ui
from callbacks import presets
from callbacks import constraints_viewer
from callbacks import i18n_callbacks
from callbacks import settings_callbacks

if __name__ == '__main__':
    app.run(debug=True, port=8051)
