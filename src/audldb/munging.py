from typing import Union, Dict, List, Tuple
from . import common
import json
import requests

from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Player:
    id: int
    team_season_id: int
    player_id: int
    jersey_number: int
    name: str
    short_name: str


@dataclass
class Pull:
    player: Union[Player, None]
    x: float
    y: float
    hangtime_ms: float


@dataclass
class Throw:
    thrower: Union[Player, None]
    receiver: Union[Player, None]
    throw_position_x: float
    throw_position_y: float
    receive_position_x: Union[float, None]
    receive_position_y: Union[float, None]
    turnover: bool
    throwaway: bool
    block: bool
    drop: bool
    goal: bool
    stall: bool


def get_pulling_team(home_point, away_point):
    if away_point[0]["t"] == 2:
        team = "away"
    elif home_point[0]["t"] == 2:
        team = "home"
    else:
        team = "unknown"

    return team


def get_receiving_team(home_point, away_point):
    if away_point[0]["t"] == 1:
        team = "away"
    elif home_point[0]["t"] == 1:
        team = "home"
    else:
        team = "unknown"

    return team


def get_scoring_team(home_point, away_point):
    if away_point[-1]["t"] == 22:
        team = "away"
    elif home_point[0]["t"] == 2:
        team = "home"
    else:
        team = "unknown"

    return team


def get_num_throwaways(point):
    return sum([1 if x["t"] == 8 else 0 for x in point])


def get_num_drops(point):
    return sum([1 if x["t"] == 19 else 0 for x in point])


def get_num_blocks(point):
    return sum([1 if x["t"] == 5 else 0 for x in point])


def get_num_completions(point):
    running_sum = 0
    for i, x in enumerate(point):
        if x["t"] == 20:
            if point[i + 1]["t"] == 20 or point[i + 1]["t"] == 22:
                running_sum += 1

    return running_sum


def get_num_possessions(point):
    running_sum = 0
    has_possession = False
    for i, x in enumerate(point):
        if i == 0 and x["t"] == 1:
            has_possession = True
            running_sum += 1

        if x["t"] == 20 and has_possession == 0:
            running_sum += 1
            has_possession = True

        if x["t"] == 8 and has_possession == 1:
            has_possession = False

    return running_sum


def get_data(url):
    # url = common.get_game_url(base_url)
    game_info = json.loads(requests.get(url).content)

    return game_info


def get_player_from_id(roster_id_map, roster_id) -> Union[Player, None]:
    if roster_id is None:
        return None
    elif roster_id < 0:
        return None
    else:
        return roster_id_map[roster_id]


class Point(object):
    def __init__(self, home_point_event, away_point_event, roster_id_map):
        self.home_point_event = home_point_event
        self.away_point_event = away_point_event

        self.pulling_team = get_pulling_team(home_point_event, away_point_event)
        self.receiving_team = get_pulling_team(home_point_event, away_point_event)
        self.scoring_team = get_scoring_team(home_point_event, away_point_event)
        self.home_players = [
            get_player_from_id(roster_id_map, roster_id)
            for roster_id in home_point_event[0]["l"]
        ]
        self.away_players = [
            get_player_from_id(roster_id_map, roster_id)
            for roster_id in away_point_event[0]["l"]
        ]

        stat_key_map = {
            "throwaways": get_num_throwaways,
            "drops": get_num_drops,
            "blocks": get_num_blocks,
            "completions": get_num_completions,
            "possessions": get_num_possessions,
        }
        self.home_stats = {k: v(home_point_event) for k, v in stat_key_map.items()}
        self.away_stats = {k: v(away_point_event) for k, v in stat_key_map.items()}

        self.play_by_play = None

    def __str__(self):
        return str(
            {
                k: self.__dict__[k]
                for k in ["pulling_team", "scoring_team", "home_stats", "away_stats"]
            }
        )


def events_per_point(events):
    points = []
    current_point = []
    for event in events:
        if event["t"] in [1, 2]:
            if current_point != []:
                # if we see a new line and the current point isn't empty
                # (occurs at the start of the game), finish the point
                # and start a new one
                points.append(current_point)
                current_point = []

        current_point.append(event)

    points.append(current_point)
    return points


def get_roster_id_map(game_info):
    roster_id_to_player = {
        x["id"]: Player(
            x["id"],
            x["team_season_id"],
            x["player_id"],
            x["jersey_number"],
            x["player"]["first_name"] + " " + x["player"]["last_name"],
            x["player"]["ext_player_id"],
        )
        for x in game_info["rostersHome"]
    }

    roster_id_to_player.update(
        {
            x["id"]: Player(
                x["id"],
                x["team_season_id"],
                x["player_id"],
                x["jersey_number"],
                x["player"]["first_name"] + " " + x["player"]["last_name"],
                x["player"]["ext_player_id"],
            )
            for x in game_info["rostersAway"]
        }
    )

    return roster_id_to_player


def return_indices(
    action,
    new_o_index,
    new_d_index,
    previous_possession,
    new_possession,
    point_over=False,
):
    if previous_possession == "o":
        return_value = action, new_o_index, new_d_index, new_possession, point_over
    elif previous_possession == "d":
        return_value = action, new_d_index, new_o_index, new_possession, point_over
    else:
        raise ValueError("previous_possession must be one of ['o', 'd']")
    
    return return_value


def change_possession(possession) -> str:
    if possession == "o":
        return_value = "d"
    elif possession == "d":
        return_value = "o"
    else:
        raise ValueError("possession must be one of ['o', 'd']")

    return return_value


def handle_next_step(
    roster_id_map,
    starting_o_event,
    starting_d_event,
    o_index,
    d_index,
    possession,
) -> Tuple[Union[None, Pull, Throw], int, int, str, bool]:

    if o_index > (len(starting_o_event) - 1) or d_index > (len(starting_d_event) - 1):
        action = None
        return return_indices(action, o_index, d_index, possession, possession, True)

    if starting_o_event[o_index]["t"] in [23, 24] or starting_d_event[d_index]["t"] in [
        23,
        24,
    ]:
        return return_indices(None, o_index, d_index, possession, possession, True)

    #     print(f"{o_index}, {d_index}, {starting_o_event[o_index]}, {starting_d_event[d_index]}")

    # assign a default so that the linter stops yelling about current_d_event being unbounded
    current_o_event: Dict = {}
    current_o_index: int = 0
    next_o_event: Dict = {}

    current_d_event: Dict = {}
    current_d_index: int = 0

    if possession == "o":
        current_o_event = starting_o_event[o_index]
        current_o_index = int(o_index)
        current_d_event = starting_d_event[d_index]
        current_d_index = int(d_index)

        # end of quarter?
        if current_o_event["t"] in [25, 26] or current_d_event["t"] in [25, 26]:
            action = None
            return return_indices(
                action, current_o_index, current_d_index, possession, possession, True
            )

        next_o_event = starting_o_event[o_index + 1]

    elif possession == "d":
        current_o_event = starting_d_event[d_index]
        current_o_index = int(d_index)
        current_d_event: Dict = starting_o_event[o_index]
        current_d_index = int(o_index)

        # end of quarter?
        if current_o_event["t"] in [25, 26] or current_d_event["t"] in [25, 26]:
            action = None
            return return_indices(
                action, current_o_index, current_d_index, possession, possession, True
            )

        next_o_event = starting_d_event[current_o_index + 1]

    else:
        raise ValueError("possession must be one of ['o', 'd']")

    if current_d_event["t"] == 3:
        player_id = current_d_event["r"] if "r" in current_d_event else None
        puller = get_player_from_id(roster_id_map, player_id)
        action = Pull(
            puller, current_d_event["x"], current_d_event["y"], current_d_event["ms"]
        )

        current_d_index += 1
        return return_indices(
            action, current_o_index, current_d_index, possession, possession
        )

    elif current_o_event["t"] == 20:
        # check if there was a throwaway
        if next_o_event["t"] == 8:
            # check if it was a block
            if current_d_event["t"] == 5:
                action = Throw(
                    get_player_from_id(roster_id_map, current_o_event["r"]),
                    None,
                    current_o_event["x"],
                    current_o_event["y"],
                    None,
                    None,
                    True,
                    True,
                    True,
                    False,
                    False,
                    False,
                )

                current_o_index += 2
                current_d_index += 1
                return return_indices(
                    action,
                    current_o_index,
                    current_d_index,
                    possession,
                    change_possession(possession),
                )
                
            # it was a throwaway
            else:
                action = Throw(
                    get_player_from_id(roster_id_map, current_o_event["r"]),
                    None,
                    current_o_event["x"],
                    current_o_event["y"],
                    next_o_event["x"],  # they log the x and y of the throwaway
                    next_o_event["y"],
                    True,
                    True,
                    False,
                    False,
                    False,
                    False,
                )

                current_o_index += 2
                current_d_index += 1
                return return_indices(
                    action,
                    current_o_index,
                    current_d_index,
                    possession,
                    change_possession(possession),
                )
            
        # check if it was a stall
        elif next_o_event["t"] == 17:
            action = Throw(
                get_player_from_id(roster_id_map, current_o_event["r"]),
                None,
                current_o_event["x"],
                current_o_event["y"],
                None,
                None,
                True,
                False,
                False,
                False,
                False,
                True,
            )

            current_o_index += 2
            current_d_index += 1
            return return_indices(
                action,
                current_o_index,
                current_d_index,
                possession,
                change_possession(possession),
            )

        # check if it was a drop
        elif next_o_event["t"] == 19:
            action = Throw(
                get_player_from_id(roster_id_map, current_o_event["r"]),
                get_player_from_id(roster_id_map, next_o_event["r"]),
                current_o_event["x"],
                current_o_event["y"],
                next_o_event["x"],
                next_o_event["y"],
                True,
                False,
                False,
                True,
                False,
                False,
            )

            # there was a case in game 2021-07-02-SEA-AUS where an 8 event followed a 19 event, 
            # which can't happen. A throw cannot be both a drop and a throwaway. So we check for this, 
            # and decide to skip that following 8 event.
            whole_o_event = starting_o_event if possession == "o" else starting_d_event
            if whole_o_event[current_o_index + 2]["t"] == 8:
                current_o_index += 3
            else:
                current_o_index += 2
            
            current_d_index += 1
            return return_indices(
                action,
                current_o_index,
                current_d_index,
                possession,
                change_possession(possession),
            )

        # check if it was a goal
        elif next_o_event["t"] == 22:
            action = Throw(
                get_player_from_id(roster_id_map, current_o_event["r"]),
                get_player_from_id(roster_id_map, next_o_event["r"]),
                current_o_event["x"],
                current_o_event["y"],
                next_o_event["x"],
                next_o_event["y"],
                False,
                False,
                False,
                False,
                True,
                False,
            )

            # don't worry about changing indices since the point is over
            return return_indices(
                action, current_o_index, current_d_index, possession, possession, True
            )

        else:
            action = Throw(
                get_player_from_id(roster_id_map, current_o_event["r"]),
                get_player_from_id(roster_id_map, next_o_event["r"]),
                current_o_event["x"],
                current_o_event["y"],
                next_o_event["x"],
                next_o_event["y"],
                False,
                False,
                False,
                False,
                False,
                False,
            )

            current_o_index += 1

            return return_indices(
                action, current_o_index, current_d_index, possession, possession
            )

    else:
        raise ValueError(
            f"Unbound event within possession: possession: {possession}, o_index: {o_index}, d_index: {d_index}, current_o_event: {current_o_event}, current_d_event: {current_d_event}, starting_o_event: {starting_o_event}, starting_d_event: {starting_d_event}")


def create_play_by_play(all_points, roster_id_map):
    numbers_care_about = [3, 5, 8, 9, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]

    play_by_play = []
    for i, point in enumerate(all_points):
        point_actions = []
        new_o_index = 0
        new_d_index = 0
        possession = "o"
        point_over = False

        pulling_team = get_pulling_team(point.home_point_event, point.away_point_event)
        starting_o_event = (
            point.away_point_event if pulling_team == "home" else point.home_point_event
        )
        starting_d_event = (
            point.home_point_event if pulling_team == "home" else point.away_point_event
        )

        starting_o_event = [
            x for x in starting_o_event[1:] if x["t"] in numbers_care_about
        ]
        starting_d_event = [
            x for x in starting_d_event[1:] if x["t"] in numbers_care_about
        ]

        while not point_over:
            try:
                action, new_o_index, new_d_index, possession, point_over = handle_next_step(
                    roster_id_map,
                    starting_o_event,
                    starting_d_event,
                    new_o_index,
                    new_d_index,
                    possession,
                )

            except Exception as e:
                print(f"Point: {all_points[i]}")
                print(f"Home events: {all_points[i].home_point_event}")
                print(f"Away events: {all_points[i].away_point_event}")
                print(f"starting_o_event: {starting_o_event}")
                print(f"starting_d_event: {starting_d_event}")
                print(f"new_o_index: {new_o_index}")
                print(f"new_d_index: {new_d_index}")
                print(f"possession: {possession}")
                raise e

            if action is not None:
                point_actions.append(action)

        play_by_play.append(point_actions)

    return play_by_play


@dataclass
class Possession:
    point: int
    index: int
    team: str
    pulling_team: bool
    starting_line: str
    turnover: bool
    throwaway: bool
    block: bool
    drop: bool
    goal: bool
    end_of_quarter: bool
    play_by_play: List


def create_possessions(points):
    possessions = []
    for point_index, point in enumerate(points):
        pulling_team = get_pulling_team(point.home_point_event, point.away_point_event)
        receiving_team = get_receiving_team(
            point.home_point_event, point.away_point_event
        )
        possession = "o"
        pulling_players = (
            point.home_players if pulling_team == "home" else point.away_players
        )
        receiving_players = (
            point.home_players if pulling_team == "away" else point.away_players
        )

        plays = [x for x in point.play_by_play]

        # check to see how many pulls are in a point
        num_pulls = len([play for play in plays if isinstance(play, Pull)])
        if num_pulls > 1:
            # make sure that all pulls are in the front. If we convert it to a binary representation of 0 and 1,
            # then we should expect the series to look like 1, 1, 0, 0, 0
            # if it looks like 1, 0, 1, 0, 0, then that's bad. 
            # we check to see if any of the running diffs is greater than 0 (i+1 - i)
            is_pull_array = [int(isinstance(play, Pull)) for play in plays]
            diffs = [y - x for (x, y) in zip(is_pull_array, is_pull_array[1:])]
            if len([x for x in diffs if x > 0]) > 0:
                raise ValueError(f"Point has pulls that are not all at front. point_index: {point_index}")


        elif num_pulls == 1:
            if not isinstance(plays[0], Pull):
                raise ValueError(f"There is a pull this point, but it's not the first play. point_index: {point_index}")

        else:
            pass

        # get rid of all of the pulls. There will not be a 
        # pull in cases where offsides happen and the other team gets
        # the disc at the brick
        plays = [play for play in plays if not isinstance(play, Pull)]

        current_o_index = 0
        current_d_index = -1
        possession_start_index = 0
        for throw_index, throw in enumerate(plays):
            if throw.turnover or throw.goal or throw_index == (len(plays) - 1):
                possessions.append(
                    Possession(
                        point_index,
                        current_o_index if possession == "o" else current_d_index,
                        receiving_team if possession == "o" else pulling_team,
                        possession == "d",
                        receiving_players if possession == "o" else pulling_players,
                        throw.turnover,
                        throw.throwaway,
                        throw.block,
                        throw.drop,
                        throw.goal,
                        True if throw_index == (len(plays) - 1) else False,
                        [x for x in plays[possession_start_index: (throw_index + 1)]],
                    )
                )

                if throw.turnover:
                    if possession == "o":
                        current_d_index += 1
                    else:
                        current_o_index += 1

                    possession = change_possession(possession)
                    possession_start_index = throw_index + 1

    return possessions


@dataclass
class ParsedEvent:
    roster_id_map: Dict
    points: List[Point]
    possessions: List[Possession]


def filter_empty_points(points):
    """Filter out points where there is not an entry with a roster"""
    filtered_points = []
    for point in points:
        events_with_roster = [event for event in point if "l" in event]
        if len(events_with_roster) > 0:
            filtered_points.append(point)

    return filtered_points


def parse_events(game_info):
    home_events = json.loads(game_info["tsgHome"]["events"])
    away_events = json.loads(game_info["tsgAway"]["events"])

    away_point_events = events_per_point(away_events)
    home_point_events = events_per_point(home_events)

    away_point_events = filter_empty_points(away_point_events)
    home_point_events = filter_empty_points(home_point_events)

    roster_id_map = get_roster_id_map(game_info)

    all_points = [
        Point(home_point_event, away_point_event, roster_id_map)
        for home_point_event, away_point_event in zip(
            home_point_events, away_point_events
        )
    ]

    play_by_play = create_play_by_play(all_points, roster_id_map)

    for point, play_by_play_point in zip(all_points, play_by_play):
        point.play_by_play = play_by_play_point

    all_possessions = create_possessions(all_points)

    return roster_id_map, all_points, all_possessions
