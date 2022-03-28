from enum import Enum
from typing import Optional


def calculate_winrate(wins, losses) -> Optional[float]:
    if wins == 0 and losses == 0:
        return None
    if losses == 0:
        return 1.0
    return wins / (wins + losses)


class Profile:
    def __init__(self, user_id, username, position, last_played, hide_rank, games_played, bio, rank, confidence, wins,
                 losses, ties):
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.rank = rank
        self.confidence = confidence
        self.user_id = user_id
        self.username = username
        self.position = position
        self.last_played = last_played
        self.hide_rank = hide_rank
        self.games_played = games_played
        self.bio = bio
        self.winrate = calculate_winrate(wins, losses)


class Outcome(Enum):
    WIN = "Win"
    LOSS = "Loss"
    TIE = "Tie"


class PlayerGameResult:
    def __init__(self, user_id: int, game_id: str, outcome: Outcome):
        self.user_id = user_id
        self.game_id = game_id
        self.outcome = outcome

    def __repr__(self):
        return f"({self.user_id}, {self.game_id}, {self.outcome})"
