from enum import Enum

from models.game import Game


class SwapError(Enum):
    USER_NOT_IN_GAME = 0
    TARGET_NOT_IN_GAME = 1


class SwapResult:
    def __init__(self, error: SwapError = None, game: Game = None, user_name=None, target_name=None):
        self.target_name = target_name
        self.user_name = user_name
        self.game = game
        self.error: SwapError = error

    @classmethod
    def error(cls, error: SwapError):
        return SwapResult(error=error)

    @classmethod
    def success(cls, game, user_name, target_name):
        return SwapResult(game=game, user_name=user_name, target_name=target_name)


class ScrambleError(Enum):
    USER_NOT_IN_GAME = 0
    INVALID_MAP_NUMBER = 1