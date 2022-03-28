from typing import Tuple

from discord import User

from cogs.queue import Queue
from models.draft_state import DraftState
from models.game import Game
from models.queue_models import UserInGame
from services import queue_service, game_service
from test.user_generators import generate_users, generate_user


def start_test_game(queue: Queue, num_games_so_far: int = 0) -> Game:
    """
    Automatically adds 10 users to the queue and starts a game
    """

    users = generate_users(10, num_games_so_far * 10)
    for user in users:
        queue_service.add(user, queue, skip_delay=True)

    return game_service.start_game(users[0], queue)


def start_test_draft_game(queue: Queue, num_games_so_far: int = 0) -> Tuple[Game, DraftState]:
    users = generate_users(10, num_games_so_far * 10)
    for user in users:
        queue_service.add(user, queue, skip_delay=True)

    return game_service.start_draft_game(queue)


def transform_user(user_in_game: UserInGame) -> User:
    return generate_user(user_in_game.user_id, user_in_game.name)
