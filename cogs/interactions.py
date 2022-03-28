from discord.ext import commands
from discord_slash.context import ComponentContext

from cogs.shared.add import add
from includes import msg, custom_ids
from models.game import GameStatus
from models.queue_models import Queue
from schemas import ingame_schema, general_schema, member_schema
from services import game_service, map_service, queue_service


class Interaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Interactions: Loaded")

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        interacted_by = ctx.author
        interaction_id = ctx.custom_id

        if interaction_id == custom_ids.shuffle_teams:
            if not ingame_schema.is_ingame(interacted_by):
                await msg.not_ingame(ctx)
                return
            if not game_service.is_captain(interacted_by):
                await msg.captains_only(ctx)
                return

            game_id = ingame_schema.get_game_id_from_user(interacted_by)
            game = game_service.get(game_id)

            if game.reshuffles > 3:
                await msg.no_more_shuffles(ctx)
                return

            game = game_service.shuffle_teams(game_id)
            await msg.new_game_started(ctx, self.bot, game, interacted_by)
        elif interaction_id == custom_ids.shuffle_map:
            if not ingame_schema.is_ingame(interacted_by):
                await msg.not_ingame(ctx)
                return
            if not game_service.is_captain(interacted_by):
                await msg.captains_only(ctx)
                return
            game_id = ingame_schema.get_game_id_from_user(interacted_by)
            new_maps = ingame_schema.new_map(game_id, map_service.get_maps(num_maps=1), 1)
            await msg.show_updated_maps(ctx, new_maps, interacted_by, 1)
        elif interaction_id == custom_ids.draft:
            if not ingame_schema.is_ingame(interacted_by):
                await msg.not_ingame(ctx)
                return
            await self.handle_draft_pick(ctx)
        elif interaction_id == custom_ids.shuffle_map_1 or interaction_id == custom_ids.shuffle_map_2:
            if not ingame_schema.is_ingame(interacted_by):
                await msg.not_ingame(ctx)
                return
            if not game_service.is_captain(interacted_by):
                await msg.captains_only(ctx)
                return

            game_id = ingame_schema.get_game_id_from_user(interacted_by)
            new_maps = ingame_schema.new_map(game_id, map_service.get_maps(num_maps=1), interaction_id)
            await msg.show_updated_maps(ctx, new_maps, interacted_by, 2)
        elif interaction_id == custom_ids.map_choices:
            if not ingame_schema.is_ingame(interacted_by):
                await msg.not_ingame(ctx)
                return
            if not game_service.is_captain(interacted_by):
                await msg.captains_only(ctx)
                return
            else:
                game_id = ingame_schema.get_game_id_from_user(interacted_by)
                game = ingame_schema.get_game(game_id)
                old_map = game['maps'][0]
                ingame_schema.choose_different_map(game_id, ctx.selected_options[0])
                await msg.display_chosen_map(ctx, game, old_map, ctx.selected_options[0])
        elif interaction_id == custom_ids.override:
            game_id = ctx.selected_options[0]
            game_service.flip_results(game_id)
            await msg.result_flipped(ctx, game_id)

        elif general_schema.check_custom_id_exists(interaction_id):
            # Get stage
            stage = general_schema.get_message_stage(interaction_id)
            if stage == 1:
                region = ctx.selected_options[0]
                member_schema.check_profile(ctx.author)
                member_schema.update_member_region(ctx.author, region)
                general_schema.update_stage(interaction_id, ctx.author, 2)

                await msg.stage1_profile_setup(ctx, interaction_id)

            elif stage == 2:
                member_schema.check_profile(ctx.author)
                member_schema.update_player_position_new(ctx.author, ctx.selected_options[0])
                general_schema.update_stage(interaction_id, ctx.author, 3)

                await msg.stage2_profile_setup(ctx, interaction_id)
            elif stage == 3:
                member_schema.check_profile(ctx.author)
                member_schema.update_stats_visibility(ctx.author, ctx.selected_options[0])
                general_schema.remove_setup(interaction_id)

                await msg.complete_setup(ctx)
        elif interaction_id == custom_ids.re_add:
            # It's the first word of the description, thankfully
            embed = ctx.origin_message.embeds[0]
            queue_name = embed.description.split()[0].lower()
            queue = Queue(queue_name)
            if not queue_service.valid_for_re_add(ctx.author):
                await msg.expired(ctx)
                return

            await add(ctx, self.bot, queue)
        else:
            await msg.expired(ctx)

    async def handle_draft_pick(self, ctx):
        game, draft_state = game_service.pick_player(ctx.author,
                                                     [int(option) for option in ctx.selected_options])
        if game.status == GameStatus.PENDING:
            for captain in game.team1_captain, game.team2_captain:
                captain_object = await self.bot.fetch_user(captain.user_id)
                captain_message_id = draft_state.messages[captain.user_id]
                message = await captain_object.fetch_message(captain_message_id)
                await message.delete()
            messages = await msg.draft_info(self.bot, game, draft_state)
            game_service.update_draft_state_messages(game.game_id, messages)
        elif game.status == GameStatus.STARTED:
            for captain in game.team1_captain, game.team2_captain:
                captain_object = await self.bot.fetch_user(captain.user_id)
                captain_message_id = draft_state.messages[captain.user_id]
                message = await captain_object.fetch_message(captain_message_id)
                await message.delete()
                await msg.dm_game_has_started(game, captain_object)
            for player in game.team1_others + game.team2_others:
                await msg.game_started_dm(self.bot, player.user_id)

            await msg.show_comp_game_started(ctx, self.bot, game)


def setup(bot):
    bot.add_cog(Interaction(bot))
