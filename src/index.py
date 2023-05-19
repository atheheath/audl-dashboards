# -*- coding: utf-8 -*-
import argparse
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import dash_auth
# from dash.dash_table.Format

from app import app

from dash.dependencies import Input, Output
from dash.dash_table.Format import Format, Scheme, Sign, Symbol

import json
import home

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

auth = dash_auth.BasicAuth(
    app,
    json.load(open("./.secrets.json", "r"))
)

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    print("Updating display page")
    print(f"root pathname: {pathname}")
    if pathname in ['/', '', '#', '/home']:
        return home.layout()
    # elif pathname == '/adp':
    #     return adp.layout()
    # elif pathname == '/aos_financing_app':
    #     return aos_financing_app.layout()
    # elif pathname == '/aos_disputes':
    #     return aos_disputes.layout()        
    else:
        return '404'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--port", "-p", default=8888)

    args = parser.parse_args()

    app.run_server(debug=True, port=args.port)
    # app.run_server(port=8888)
