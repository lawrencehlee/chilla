from includes import msg
from models.queue_models import Queue, AddStatus
from services import queue_service, game_service


async def add(ctx, bot, queue: Queue):
    user = ctx.author
    add_result = queue_service.add(user, queue)
    if add_result.status == AddStatus.ALREADY_IN_QUEUE:
        await msg.refreshed_add(ctx, queue.value)
        return
    if add_result.status == AddStatus.ALREADY_IN_GAME:
        await msg.already_ingame(ctx)
        return
    if add_result.status == AddStatus.DELAYED:
        await msg.delayed_add(ctx, add_result.delay_seconds)
        return

    if add_result.should_start():
        if queue in (Queue.QUICKPLAY, Queue.TEST, Queue.NEWBLOODS):
            await msg.generating_teams(ctx, bot)
            game = game_service.start_game(user, queue)

            await msg.game_started(ctx, bot, game)
            for player in game.team1_players + game.team2_players:
                await msg.game_started_dm(bot, player.user_id)
            return
        else:
            raise ValueError("Invalid queue?")

    await msg.added_to_queue(ctx, bot, add_result.queue.value, add_result.queue_count)
