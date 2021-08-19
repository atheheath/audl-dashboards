import urllib.parse
import plotly.graph_objects as go
from dataclasses import dataclass
from typing import Dict, List


def root_audl_url():
    return "https://audl-stat-server.herokuapp.com/stats-pages/game/"


def sol_games():
    return ["2021-06-25-AUS-SEA", "2021-06-26-AUS-SJ", "2021-06-25-DAL-LA"]


def get_game_url(game_base_url):
    return urllib.parse.urljoin(root_audl_url(), game_base_url)
