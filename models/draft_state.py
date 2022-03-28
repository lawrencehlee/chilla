from abc import ABC, abstractmethod
from typing import Dict


class DraftState:
    def __init__(self, game_id: int, team_to_pick: int, num_picks: int, messages: Dict[int, int]):
        self.game_id = game_id
        self.team_to_pick = team_to_pick
        self.num_picks = num_picks
        self.messages = messages


class PickOrder(ABC):
    @abstractmethod
    def num_picks(self, num_players_left: int):
        pass


class BalancedPickOrder(PickOrder):
    """
    1, 2, 2, 2, 1
    """

    def num_picks(self, num_players_left: int):
        if num_players_left == 8 or num_players_left == 1:
            return 1
        return 2
