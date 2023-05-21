import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State

# from app import app

from . import common


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


# # add callback for toggling the collapse on small screens
# @app.callback(
#     Output("navbar-collapse", "is_open"),
#     [Input("navbar-toggler", "n_clicks")],
#     [State("navbar-collapse", "is_open")],
# )
# def toggle_navbar_collapse(n, is_open):
#     if n:
#         return not is_open
#     return is_open