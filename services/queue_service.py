from datetime import datetime

from discord import User

from models.queue_models import Queue, AddResult, AddStatus
from schemas import member_schema, queue_schema, ingame_schema


def add(user: User, queue: Queue, skip_delay=False) -> AddResult:
    member_schema.check_profile(user)
    if queue_schema.check_if_in_queue(user, queue):
        queue_schema.refresh_add(user, queue)
        return AddResult.status(AddStatus.ALREADY_IN_QUEUE, queue)
    if ingame_schema.is_ingame(user):
        return AddResult.status(AddStatus.ALREADY_IN_GAME, queue)

    profile = member_schema.get_profile(user)
    delay_target = profile.get('delayTarget')
    if not skip_delay and delay_target:
        now = datetime.now()
        if delay_target > now:
            return AddResult.status(AddStatus.DELAYED, queue, delay_seconds=(delay_target - now).seconds)

    queue_schema.add_to_queue(user, queue)
    queue_count = queue_schema.get_queue_count(queue)

    return AddResult.added(queue_count, queue)


def valid_for_re_add(user: User):
    most_recent_games = ingame_schema.get_recent_games(1)
    if len(most_recent_games) == 0:
        return False

    game = most_recent_games[0]
    user_ids = member_schema.query_user_ids_who_have_played_in_games([game.game_id])

    return user.id in user_ids
