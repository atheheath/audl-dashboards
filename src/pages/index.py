# -*- coding: utf-8 -*-
import argparse
import dash
import dash_bootstrap_components as dbc
from dash import html

from dash.dependencies import Input, Output
from dash.dash_table.Format import Format, Scheme, Sign, Symbol

import json
import os

dash.register_page(__name__, path="/")

layout = html.Div(children=[
    html.H1(children='This is our Home page'),

    html.Div(children='''
        This is our Home page content.
    '''),

])
