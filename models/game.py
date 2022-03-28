from enum import Enum
from typing import List

from models.queue_models import Queue, UserInGame


class GameStatus(Enum):
    PENDING = 1
    STARTED = 2
    FINISHED = 3


class Game:
    def __init__(self, game_id: int, started_at, queue: Queue, team1_players: List[UserInGame],
                 team2_players: List[UserInGame], maps: List[str], ended_at, status: GameStatus,
                 unassigned_players: List[UserInGame] = [], reshuffles: int = 0):
        self.unassigned_players = unassigned_players
        self.status = status
        self.ended_at = ended_at
        self.started_at = started_at
        self.maps = maps
        self.team2_players = team2_players
        self.team1_players = team1_players

        self.team1_captain = next(iter([player for player in self.team1_players if player.is_captain]), None)
        self.team2_captain = next(iter([player for player in self.team2_players if player.is_captain]), None)
        self.team1_others = [player for player in self.team1_players if not player.is_captain]
        self.team2_others = [player for player in self.team2_players if not player.is_captain]
        self.queue = queue
        self.game_id = game_id
        self.reshuffles = reshuffles

    def get_team1_captain_name(self) -> str:
        return self.team1_captain.name if self.team1_captain else None

    def get_team2_captain_name(self) -> str:
        return self.team2_captain.name if self.team1_captain else None

    def get_team1_others_names(self) -> List[str]:
        return [player.name for player in self.team1_others]

    def get_team2_others_names(self) -> List[str]:
        return [player.name for player in self.team2_others]

    def get_all_players(self) -> List[UserInGame]:
        return self.team1_players + self.team2_players

    def is_on_team1(self, user_id):
        return user_id in [player.user_id for player in self.team1_players]

    def is_on_team2(self, user_id):
        return user_id in [player.user_id for player in self.team2_players]


class EmptyGame:
    """
    Intended for situations in which the players in a game are undetermined or unknown
    """

    def __init__(self, game_id, started_at, queue: Queue, ended_at, status: GameStatus, maps: List[str]):
        self.status = status
        self.ended_at = ended_at
        self.started_at = started_at
        self.queue = queue
        self.game_id = game_id
        self.maps = maps


class FinishedGame:
    def __init__(self, game: EmptyGame, winners: List[str], losers: List[str], tie: bool, ended_at):
        self.game = game
        self.winners = winners
        self.losers = losers
        self.tie = tie
        self.ended_at = ended_at
