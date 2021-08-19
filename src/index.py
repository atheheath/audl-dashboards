# -*- coding: utf-8 -*-
import argparse
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table

from app import app

from dash.dependencies import Input, Output
from dash_table.Format import Format, Scheme, Sign, Symbol

import home
# import adp
# import aos_financing_app
# import aos_disputes

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    print("Updating display page")
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
