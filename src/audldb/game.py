import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

import numpy as np
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# from app import app
# from common import DataHolder, cache_dir, generate_dash_table, load_data
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots


def plot_field(fig=None, multi_factor=8, include_thirds=False):

    if fig is None:
        fig = go.Figure()

    fig.update_layout(
        yaxis=go.layout.YAxis(
            range=[-10, 110],
            showgrid=False,
            zeroline=False,
            showline=False,
            linecolor='#636363',
            linewidth=6,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        ),
        xaxis=go.layout.XAxis(
            range=[0, 53.33],
            showgrid=False,
            zeroline=False,
            showline=False,
            linecolor='#636363',
            linewidth=6,
            showticklabels=False,
            
        ),
        margin=dict(
            l=0,
            r=0,
            b=0,
            t=0,
            pad=10
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig.add_shape(
        type="rect",
        x0=0,
        y0=-10,
        x1=53.33,
        y1=10,
        fillcolor="White",
        line=dict(
            color="Black",
            width=2,
        ),
        layer="below"
    )

    fig.add_shape(
        type="rect",
        x0=0,
        y0=10,
        x1=53.33,
        y1=90,
#         fillcolor="Green",
        fillcolor="White",
        line=dict(
            color="Black",
            width=2,
        ),
        layer="below",
    )

    fig.add_shape(
        type="rect",
        x0=0,
        y0=90,
        x1=53.33,
        y1=110,
        fillcolor="White",
        line=dict(
            color="Black",
            width=2,
        ),
        layer="below",
    )

#     for i in range(10, 100, 10):
#         if i == 10 or i == 90:
#             line_width = 3
#         else:
#             line_width = 1

#         fig.add_shape(
#             type="line",
#             x0=0,
#             y0=i,
#             x1=53.33,
#             y1=i,
#             line=dict(
#                 color="White",
#                 width=line_width,
#             )
#         )

    if include_thirds:
        fig.add_shape(
            type="line",
            x0=53.33 / 3,
            y0=-10,
            x1=53.33 / 3,
            y1=110,
            line=dict(
                color="Black",
                width=3,
                dash="dash"
            )
        )
        
        fig.add_shape(
            type="line",
            x0=53.33 / 3 * 2.,
            y0=-10,
            x1=53.33 / 3 * 2.,
            y1=110,
            line=dict(
                color="Black",
                width=3,
                dash="dash"
            )
        )
    return fig


def determine_color(throw, receiver=False):
    if throw.throwaway:
        return "red"
    elif throw.stall:
        return "blue"
    elif throw.drop and receiver:
        return "orange"
    elif throw.goal and receiver:
        return "green"
    elif throw.goal:
        return "magenta"
    return "black"


def determine_name(throw, receiver=False):
    if throw.throwaway:
        return "Throwaway"
    if throw.stall:
        return "Stall"
    elif throw.drop and receiver:
        return "Drop"
    elif throw.goal and receiver:
        return "Goal"
    elif throw.goal:
        return "Assist"
    return "Completion"


def get_data_to_plot(throws):
    throw_points_y = [throw.throw_position_y - 10 for throw in throws]   
    throw_points_x = [throw.throw_position_x + 53.33 / 2 for throw in throws]
    
    throwers = [throw.thrower.short_name for throw in throws]
    hover_text = [f"id: {throw.thrower.short_name}, goal: {throw.goal}\n turnover: {throw.turnover}, drop: {throw.drop}" for throw in throws]
    colors = [determine_color(throw) for throw in throws]
    name = determine_name(throws[0]) if len(throws) > 0 else ""
        
    return throw_points_x, throw_points_y, throwers, hover_text, colors, name


def plot_possession(fig, possession):
    throws = [x for x in possession.play_by_play]
    completions = [x for x in throws if not x.throwaway and not x.goal]
    goals = [x for x in throws if not x.turnover and x.goal]
    throwaways = [x for x in throws if x.throwaway and not x.drop]
    drops = [x for x in throws if x.drop]
    stalls = [x for x in throws if x.stall]
    
    for plays in [completions, throwaways, goals]:
        throw_points_x, throw_points_y, throwers, hover_text, colors, name = get_data_to_plot(plays)

        fig.add_trace(
            go.Scatter(
                x=throw_points_x,
                y=throw_points_y,
                mode='markers+text',
                text=throwers,
                textposition="top center",
                hovertext=hover_text,
                marker_size=10,
                marker_color=colors,
                name=name
            )
        )
        
    # plot all of the lines
    throw_points_x, throw_points_y, throwers, hover_text, colors, name = get_data_to_plot(throws)

    fig.add_trace(
        go.Scatter(
            x=throw_points_x,
            y=throw_points_y,
            mode='lines',
#             text=throwers,
#             textposition="middle center",
#             hovertext=hover_text,
#             marker_size=10,
#             marker_color=colors,
            line=dict(
                color="Black",
                width=1,
            ),
            showlegend=False
        )
    )    
    
    
    # plot the goals
    if len(goals) > 0:
        goal = goals[0]
        fig.add_trace(
            go.Scatter(
                x=[goal.receive_position_x + 53.33 / 2],
                y=[goal.receive_position_y - 10],
                mode='markers+text',
                text=[goal.receiver.short_name],
                textposition="top center",
                hovertext=f"{goal.receiver.short_name}",
                marker_size=10,
                marker_color=determine_color(goal, receiver=True),
                name=determine_name(goal, receiver=True)
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[x + 53.33 / 2 for x in [goal.throw_position_x, goal.receive_position_x]],
                y=[y - 10 for y in [goal.throw_position_y, goal.receive_position_y]],
                mode='lines',
                line=dict(
                    color="green",
                    width=1
                ),
                showlegend=False
            ),
        )
        
    # plot the drops
    elif len(drops) > 0:
        drop = drops[0]
        fig.add_trace(
            go.Scatter(
                x=[drop.receive_position_x + 53.33 / 2],
                y=[drop.receive_position_y - 10],
                mode='markers+text',
                text=[drop.receiver.short_name],
                textposition="top center",
                hovertext=f"{drop.receiver.short_name}",
                marker_size=10,
                marker_color=determine_color(drop, receiver=True),
                name=determine_name(drop, receiver=True)
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[x + 53.33 / 2 for x in [completions[-1].throw_position_x, completions[-1].receive_position_x]],
                y=[y - 10 for y in [completions[-1].throw_position_y, completions[-1].receive_position_y]],
                mode='lines',
                line=dict(
                    color="orange",
                    width=1
                ),
                showlegend=False
            ),
        )

    
    # plot the stalls
    elif len(stalls) > 0:
        stall = stalls[0]
        fig.add_trace(
            go.Scatter(
                x=[stall.receive_position_x + 53.33 / 2],
                y=[stall.receive_position_y - 10],
                mode='markers+text',
                text=[stall.receiver.short_name],
                textposition="top center",
                hovertext=f"{stall.receiver.short_name}",
                marker_size=10,
                marker_color=determine_color(stall, receiver=True),
                name=determine_name(stall, receiver=True)
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[x + 53.33 / 2 for x in [completions[-1].throw_position_x, completions[-1].receive_position_x]],
                y=[y - 10 for y in [completions[-1].throw_position_y, completions[-1].receive_position_y]],
                mode='lines',
                line=dict(
                    color="orange",
                    width=1
                ),
                showlegend=False
            ),
        )


    # plot the throwaways
    elif len(throwaways) > 0:
        throwaway = throwaways[0]
        
        if throwaway.receive_position_x is not None and throwaway.receive_position_y is not None:
            
            fig.add_trace(
                go.Scatter(
                    x=[x + 53.33 / 2 for x in [throwaway.throw_position_x, throwaway.receive_position_x]],
                    y=[y - 10 for y in [throwaway.throw_position_y, throwaway.receive_position_y]],
                    mode='lines',
                    line=dict(
                        color="red",
                        width=1
                    ),
                    showlegend=False
                ),
            )

    text_to_combine = [
        f"Point: {possession.point + 1}",
        f"Team: {possession.team.capitalize()}",
        f"Possession on this point: {possession.index + 1}",
        f"Team pulled: {possession.pulling_team}",
        f"Num throws: {len(possession.play_by_play)}"
    ]

    fig.update_layout(
        annotations=[
            go.layout.Annotation(
                text="<br>".join(text_to_combine),
                align="left",
                xref="paper",
                yref="paper",
                x=0.2,
                y=0.5,
                bordercolor="black",
                borderwidth=1
            )
        ]
    )

    return fig
