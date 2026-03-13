import dash
import dash_bootstrap_components as dbc
from components.sidebar import create_sidebar
from components.viewer import create_viewer

# Инициализация приложения (LUMEN - чистая светлая тема, похожая на оригинал)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUMEN], suppress_callback_exceptions=True)
app.title = "TabletCAD Pro"

# Собираем Layout из компонентов
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(create_sidebar(), width=3, className="bg-light border-end", style={"height": "100vh", "overflow-y": "auto", "padding": "20px"}),
                dbc.Col(create_viewer(), width=9, style={"height": "100vh", "padding": "20px"})
            ],
            className="g-0"
        )
    ],
    fluid=True,
    className="g-0"
)

# Импортируем коллбеки, чтобы они зарегистрировались в app
from callbacks import ui_updater
from callbacks import graph_updater
from callbacks import plotly_ui
from callbacks import presets
from callbacks import constraints_viewer

if __name__ == '__main__':
    app.run(debug=True, port=8051)
