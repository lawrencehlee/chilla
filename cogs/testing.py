from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice

import config
from includes import msg
from schemas import testing_schema, ingame_schema
from services import game_service


class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Testing: Loaded")

    @cog_ext.cog_slash(
        name="addplayers",
        description="Testing only: Adds players to queue",
        options=[
            create_option(
                name="queue",
                description="Select a queue",
                required=True,
                option_type=3,
                choices=config.queues(True)
            ),
            create_option(
                name="amount",
                description="Select a queue",
                required=True,
                option_type=3,
                choices=[
                    create_choice(
                        name="1",
                        value="1"
                    ),
                    create_choice(
                        name="2",
                        value="2"
                    ),
                    create_choice(
                        name="3",
                        value="3"
                    ),
                    create_choice(
                        name="4",
                        value="4"
                    ),
                    create_choice(
                        name="5",
                        value="5"
                    ),
                    create_choice(
                        name="6",
                        value="6"
                    ),
                    create_choice(
                        name="7",
                        value="7"
                    ),
                    create_choice(
                        name="8",
                        value="8"
                    ),
                    create_choice(
                        name="9",
                        value="9"
                    ),
                    create_choice(
                        name="10",
                        value="10"
                    ),
                ]
            )
        ],
        guild_ids=config.variables['guild_ids']
    )
    async def _addplayers(self, ctx: SlashContext, queue: str, amount: str):
        amount = int(amount)
        testing_schema.add_test_players(queue, amount)
        await msg.success(ctx, f"Added **{amount}** players to **`{queue}`**")

    @cog_ext.cog_slash(
        name="draft",
        description="Developers only: Force send draft info dms",
        guild_ids=config.variables['guild_ids']
    )
    async def _draft(self, ctx: SlashContext):
        game_id = ingame_schema.get_game_id_from_user(ctx.author)
        game, draft_state = game_service.get_game_and_draft_state(game_id)
        messages = await msg.draft_info(self.bot, game, draft_state)
        game_service.update_draft_state_messages(game.game_id, messages)
        await ctx.send("DMs sent", hidden=True)

    @cog_ext.cog_slash(
        name="reset",
        description="Developers only: Resets everything",
        guild_ids=config.variables['guild_ids']
    )
    async def _reset(self, ctx: SlashContext):
        testing_schema.reset_everything()
        await msg.success(ctx, "Everything has been **reset**!")

    @cog_ext.cog_slash(
        name="gs",
        description="Game Start UI",
        guild_ids=config.variables['guild_ids']
    )
    async def _gs(self, ctx: SlashContext):
        await msg.gs(ctx, self.bot)

    @cog_ext.cog_slash(
        name="forcecaptain",
        description="Make me the captain!!",
        guild_ids=config.variables['guild_ids']
    )
    async def _force_captain(self, ctx: SlashContext):
        testing_schema.force_captain(ctx.author.id)
        await msg.success(ctx, "I'm the captain now")


def setup(bot):
    bot.add_cog(Testing(bot))
