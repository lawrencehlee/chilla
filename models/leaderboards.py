from datetime import date
from typing import List, Optional, Tuple

from models.profile import calculate_winrate


class Leaderboard:
    def __init__(self, start_date: Optional[date], end_date: Optional[date], total_games: int,
                 most_popular_maps: List[Tuple[str, int]], most_games_played: List[Tuple[str, int]],
                 most_games_won: List[Tuple[str, int]], highest_winrate: List[Tuple[str, float]], unique_players: int):
        self.start_date = start_date
        self.end_date = end_date
        self.total_games = total_games
        self.most_games_played = most_games_played
        self.most_games_won = most_games_won
        self.highest_winrate = highest_winrate
        self.most_popular_maps = most_popular_maps
        self.unique_players = unique_players


class PlayerStatsInLeaderboard:
    def __init__(self, user_id: int, username: str, total_games: int, wins: int, losses: int, ties: int):
        self.user_id = user_id
        self.username = username
        self.total_games = total_games
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.winrate = calculate_winrate(wins, losses)

    def with_win(self):
        return PlayerStatsInLeaderboard(self.user_id, self.username, self.total_games + 1, self.wins + 1,
                                        self.losses, self.ties)

    def with_loss(self):
        return PlayerStatsInLeaderboard(self.user_id, self.username, self.total_games + 1, self.wins,
                                        self.losses + 1, self.ties)

    def with_tie(self):
        return PlayerStatsInLeaderboard(self.user_id, self.username, self.total_games + 1, self.wins,
                                        self.losses, self.ties + 1)
