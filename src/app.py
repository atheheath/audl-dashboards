import dash
import dash_bootstrap_components as dbc
import dash_auth
import os
from dash import html
from dash import dcc

app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    use_pages=True
)

app.config.suppress_callback_exceptions = True

auth = dash_auth.BasicAuth(
    app,
    {os.environ["LOGIN_USERNAME"]: os.environ["LOGIN_PASSWORD"]}
)

app.layout = html.Div([
	html.H1('Multi-page app with Dash Pages'),
    html.Div(
        [
            html.Div(
                dcc.Link(
                    f"{page['name']} - {page['path']}", href=page["relative_path"]
                )
            )
            for page in dash.page_registry.values()
        ]
    ),
	dash.page_container
])

server = app.server


if __name__ == '__main__':
	app.run_server(debug=True)
