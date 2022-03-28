import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice

import config
from includes import msg
from includes.general import correct_channel
from models.ingame_models import SwapResult, SwapError
from models.profile import Outcome
from models.queue_models import Queue
from schemas import member_schema, ingame_schema
from services import game_service


class Ingame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Ingame: Loaded")

    @cog_ext.cog_slash(
        name="games",
        description="View current games",
        options=[
            create_option(
                name="queue",
                description="Choose a queue: [optional]",
                required=False,
                option_type=3,
                choices=config.queues(True)
            )
        ],
        guild_ids=config.variables['guild_ids']
    )
    async def _games(self, ctx: SlashContext, queue: str = None):
        if not await correct_channel(ctx, ctx.author):
            return

        games = game_service.get_games(Queue(queue) if queue else None)
        await msg.games_info(ctx, games)

    @cog_ext.cog_slash(
        name="finish",
        description="Finish the game you're in",
        options=[
            create_option(
                name="outcome",
                description="The game's outcome",
                required=True,
                option_type=3,
                choices=[
                    create_choice(
                        name="Win",
                        value=Outcome.WIN.value
                    ),
                    create_choice(
                        name="Loss",
                        value=Outcome.LOSS.value
                    ),
                    create_choice(
                        name="Tie",
                        value=Outcome.TIE.value
                    )
                ]
            )
        ],
        guild_ids=config.variables['guild_ids']
    )
    async def _finish(self, ctx: SlashContext, outcome: str):
        if not await correct_channel(ctx, ctx.author):
            return

        game = game_service.finish(ctx.author, Outcome(outcome))

        if game is None:
            await msg.not_ingame(ctx)
            return

        await msg.game_finished(ctx, self.bot, game.queue, game.started_at, game.ended_at, outcome)

    @cog_ext.cog_slash(
        name="swap",
        description="Swap teams with another player",
        guild_ids=config.variables['guild_ids'],
        options=[
            create_option(
                name="member",
                description="Choose a player",
                required=True,
                option_type=6
            )
        ]
    )
    async def _swap(self, ctx: SlashContext, member: discord.Member):
        if not await correct_channel(ctx, ctx.author):
            return

        user = ctx.author
        swap_result: SwapResult = game_service.swap(user, member)
        if swap_result.error == SwapError.USER_NOT_IN_GAME:
            await msg.not_ingame(ctx)
            return
        if swap_result.error == SwapError.TARGET_NOT_IN_GAME:
            await msg.other_not_ingame(ctx)
            return

        await msg.swapped(ctx, self.bot, user.name, member.name)

    @cog_ext.cog_slash(
        name="sub",
        description="Sub a player ingame",
        guild_ids=config.variables['guild_ids'],
        options=[
            create_option(
                name="member",
                description="Player you want to sub",
                required=True,
                option_type=6
            )
        ]
    )
    async def _sub(self, ctx: SlashContext, member: discord.Member):
        if not await correct_channel(ctx, ctx.author):
            return

        user = ctx.author
        if ingame_schema.is_ingame(user):
            await ctx.send("You're already ingame.", hidden=True)
        else:
            if ingame_schema.is_ingame(member) == False:
                await ctx.send(f"**{member.name}** isn't ingame.", hidden=True)
            else:
                member_schema.check_profile(user)
                # sub player
                if ingame_schema.check_if_comp_game_by_user(member):
                    return await ctx.send("You can't sub players while drafting is going on", hidden=True)
                ingame_schema.sub_player(user, member)
                embed = discord.Embed(description=f"**{user.name}** has subbed **{member.name}**")
                for guild in self.bot.guilds:
                    if guild.name == ctx.guild.name:
                        await ctx.send(embed=embed)
                    else:
                        channel = discord.utils.get(guild.text_channels, name=config.variables['channel'])
                        if channel is not None:
                            await channel.send(embed=embed)


def setup(cog):
    cog.add_cog(Ingame(cog))
