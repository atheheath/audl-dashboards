from ast import parse
from audldb import common, game, get_audl_stats, munging
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html, callback
import numpy as np
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import posixpath

from functools import lru_cache

from dataclasses import dataclass


from dash.dependencies import Input, Output
from plotly.subplots import make_subplots

dash.register_page(__name__, path="/home")

@dataclass
class DataHolder:
    data: munging.ParsedEvent


game_info = DataHolder(munging.ParsedEvent({}, [], []))


# fig_loss_rates = generate_line_graph(data_table.data)
fig_field_plot = game.plot_field()


@lru_cache()
def get_game_urls():
    return list(sorted(get_audl_stats.get_audl_stat_urls()))


all_game_urls = get_game_urls()

body = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                dcc.Dropdown(
                    id='demo-dropdown',
                    options=[
                        {'label': posixpath.split(url)[-1], 'value': url}
                        for url in all_game_urls
                    ],
                    value=None
                )
            ]),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.H2("Home"),
            html.Div(
                id='live-update-text',
            )
            # html.Button("Refresh Data", id="home-main-data-table-refresh"),
        ])
    ]),
    dcc.Loading(
        id="home-main-loading",
        type="default",
        children=[
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="fig-field-plot",
                        figure=fig_field_plot
                    ),
                    html.Div(
                        id="fig-slider-index",
                        children=[
                            dcc.Slider(
                                id='fig-slider',
                                min=-1,
                                max=0.0,
                                step=1.0,
                                value=-1,
                                # marks={0: '0', 180: '180', 360: '360'},
                                updatemode='drag',
                            ),
                        ],
                        # style=dict(width='50%'),
                    )
                ]),
            ])
        ]
    )
])


def layout():
    # load_data(data_table, cache_dir, home_queries.data_query)
    return html.Div([
        navbar(),
        body
    ])


def navbar():
    # make a reuseable dropdown for the different examples
    dropdown = dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem(dbc.NavLink("Home", href="/home/new")),
        ] + [
            dbc.DropdownMenuItem(dbc.NavLink(f"{base_url}", href=f"/{base_url}"))
            for base_url in common.sol_games()
        ],
        nav=True,
        in_navbar=True,
        label="Pages",
    )

    # # make a reuseable dropdown for the different examples
    # dropdown = dbc.DropdownMenu(
    #     children=[
    #         dbc.DropdownMenuItem("Entry 1"),
    #         dbc.DropdownMenuItem("Entry 2"),
    #         dbc.DropdownMenuItem(divider=True),
    #         dbc.DropdownMenuItem("Entry 3"),
    #     ],
    #     nav=True,
    #     in_navbar=True,
    #     label="Menu",
    # )

    # this is the default navbar style created by the NavbarSimple component
    default = dbc.NavbarSimple(
        # children=[home, adp],
        children=[dropdown],
        brand="Sol Games",
        brand_href="/home",
        sticky="top",
        className="mb-5",
    )

    return default

@callback(
        # Output("home-game-info", "data"),
        # Output("fig-field-plot", "figure"),
    Output(component_id='live-update-text', component_property='children'),
    Output(component_id='fig-slider-index', component_property='children'),
    Input('demo-dropdown', 'value')
)
def update_game_data(value):
    if value is None:
        return [
            [html.Span("Please select game from dropdown")],
            dcc.Slider(
                id='fig-slider',
                min=-1,
                max=0.0,
                step=1.0,
                value=-1,
                updatemode='drag',
            )
        ]

    else:
        print(f"Getting game data for url: {value}")
        parsed_event = munging.parse_events(munging.get_data(value))
        
        game_info.data = munging.ParsedEvent(*parsed_event)

        return [html.Span(f"Game is {value}"), html.Span(f"Num possessions is {len(game_info.data.possessions)}")], dcc.Slider(
                id='fig-slider',
                min=1,
                max=len(game_info.data.possessions),
                step=1.0,
                value=1,
                marks={1: '1', len(game_info.data.possessions): str(len(game_info.data.possessions))},
                updatemode='drag',
            )
        


@callback(
    Output("fig-field-plot", "figure"),
    Input('fig-slider', 'value')
)
def update_possession_plot(value):
    if value == -1:  # happens when first loading
        return fig_field_plot

    else:

        fig = game.plot_field()
        fig = game.plot_possession(fig, game_info.data.possessions[value - 1])

        return fig

