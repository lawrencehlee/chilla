import calendar
import datetime
from typing import List, Tuple

from models.game import EmptyGame
from models.leaderboards import Leaderboard, PlayerStatsInLeaderboard
from models.profile import PlayerGameResult, Outcome
from schemas import member_schema
from services import game_service

NUM_TOP_RESULTS = 10


def get_leaderboard(year: int = None, month: int = None) -> Leaderboard:
    # Neither - default to all time
    if year is None and month is None:
        start_date = None
        end_date = None
    else:
        # No year - default to current
        if year is None and month is not None:
            year = datetime.datetime.now().year

        # No month - default to whole year
        if month is None and year is not None:
            start_date = datetime.date(year, 1, 1)
            end_date = datetime.date(year, 12, 31)
        else:
            start_date = datetime.date(year, month, 1)
            end_date = datetime.date(year, month, calendar.monthrange(year, month)[1])

    games: List[EmptyGame] = game_service.query_empty(start_date, end_date)
    player_stats = calculate_player_stats(member_schema.query_player_game_results([game.game_id for game in games]))
    return Leaderboard(start_date, end_date, len(games), calculate_popular_maps(games),
                       find_players_with_most_games(player_stats), find_players_with_most_wins(player_stats),
                       find_players_with_highest_winrates(player_stats), len(player_stats))


def calculate_popular_maps(games: List[EmptyGame]) -> List[Tuple[str, int]]:
    map_frequencies = {}
    for game in games:
        for m in game.maps:
            map_frequencies[m] = map_frequencies.get(m, 0) + 1

    sorted_desc = sorted(map_frequencies.items(), key=lambda pair: pair[1], reverse=True)
    return [(pair[0], pair[1]) for pair in sorted_desc[:3]]


def calculate_player_stats(player_game_results: List[PlayerGameResult]) -> List[PlayerStatsInLeaderboard]:
    by_user_id = {}
    for result in player_game_results:
        if result.user_id not in by_user_id:
            profile_raw = member_schema.get_profile_by_id(result.user_id)
            by_user_id[result.user_id] = PlayerStatsInLeaderboard(result.user_id, profile_raw["username"], 0, 0, 0, 0)

        existing = by_user_id[result.user_id]
        if result.outcome == Outcome.WIN:
            by_user_id[result.user_id] = existing.with_win()
        elif result.outcome == Outcome.LOSS:
            by_user_id[result.user_id] = existing.with_loss()
        elif result.outcome == Outcome.TIE:
            by_user_id[result.user_id] = existing.with_tie()

    return list(by_user_id.values())


def find_players_with_highest_winrates(player_stats: List[PlayerStatsInLeaderboard]) -> List[Tuple[str, float]]:
    players_with_winrates = [player for player in player_stats if player.winrate is not None]
    sorted_by_winrate_desc = sorted(players_with_winrates, key=lambda player: player.winrate, reverse=True)
    sorted_players_with_min_num_games = [player for player in sorted_by_winrate_desc if player.total_games >= 5]
    if len(sorted_players_with_min_num_games) >= NUM_TOP_RESULTS:
        return [(player.username, player.winrate) for player in sorted_players_with_min_num_games][:NUM_TOP_RESULTS]

    return [(player.username, player.winrate) for player in sorted_by_winrate_desc][:NUM_TOP_RESULTS]


def find_players_with_most_games(player_stats: List[PlayerStatsInLeaderboard]) -> List[Tuple[str, int]]:
    sorted_by_games_desc = sorted(player_stats, key=lambda player: player.total_games, reverse=True)[:NUM_TOP_RESULTS]
    return [(player.username, player.total_games) for player in sorted_by_games_desc]


def find_players_with_most_wins(player_stats: List[PlayerStatsInLeaderboard]) -> List[Tuple[str, int]]:
    sorted_by_wins_desc = sorted(player_stats, key=lambda player: player.wins, reverse=True)[:NUM_TOP_RESULTS]
    return [(player.username, player.wins) for player in sorted_by_wins_desc]
