import uuid

import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import MenuContext
from discord_slash.model import ContextMenuType

import config
from cogs.shared.add import add
from includes import msg, general
from models.queue_models import Queue as QueueEnum
from schemas import queue_schema, general_schema, member_schema


class CommandContextMenus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("CommandContextMenus Cog: Loaded")

    @cog_ext.cog_context_menu(
        target=ContextMenuType.MESSAGE,
        name="Add Quickplay",
        guild_ids=config.variables['guild_ids']
    )
    async def _add_quickplay(self, ctx: MenuContext):
        user = ctx.author
        if not await general.correct_channel(ctx, user):
            return

        queue_enum = QueueEnum("quickplay")
        await add(ctx, self.bot, queue_enum)

    @cog_ext.cog_context_menu(
        target=ContextMenuType.MESSAGE,
        name="Delete Quickplay",
        guild_ids=config.variables['guild_ids']
    )
    async def _del_quickplay(self, ctx: MenuContext):
        user = ctx.author
        if not await general.correct_channel(ctx, user):
            return
        queue = "quickplay"
        queue_schema.remove_from_queue(user, queue)
        await msg.removed_from_single_queue(ctx, self.bot, queue, queue_schema.get_queue_count(QueueEnum(queue)))

    @cog_ext.cog_context_menu(
        target=ContextMenuType.MESSAGE,
        name="View Queue Status",
        guild_ids=config.variables['guild_ids']
    )
    async def _view_status(self, ctx: MenuContext):
        user = ctx.author
        if not await general.correct_channel(ctx, user):
            return
        queues = [QueueEnum.QUICKPLAY.value, QueueEnum.NEWBLOODS.value, QueueEnum.TEST.value]
        embed = discord.Embed(color=msg.success_color)
        for q in queues:
            is_live = queue_schema.queue_is_ingame(q)
            players = []
            for player in queue_schema.get_queue_players(q):
                games_played = member_schema.get_profile_by_id(player['userId'])['gamesPlayed']
                players.append(f"{config.variables['rank']} **`{games_played}`** **`{player['username'][:14]}`**")
            embed.add_field(
                name=f"{config.variables['live'] if is_live else ''}**{q.upper()}** **`[{queue_schema.get_queue_count(QueueEnum(q))}/10]`**",
                value="**`OPEN`**" if len(players) < 1 else '\n'.join(players))

        await ctx.send(embed=embed)

    @cog_ext.cog_context_menu(
        target=ContextMenuType.MESSAGE,
        name="Profile Setup",
        guild_ids=config.variables['guild_ids']
    )
    async def _profile_setup(self, ctx: MenuContext):
        if await general.correct_channel(ctx, ctx.author) == False:
            return
        if general_schema.check_setup_exists(ctx.author):
            return await ctx.send("Setup already in progress. Check your DM's", hidden=True)
        unique_id = str(uuid.uuid4())
        try:
            await msg.profile_setup(ctx.author, unique_id)
        except Exception as e:
            print(e)
        general_schema.add_profile_setup(ctx.author, str(unique_id), 1)
        embed = discord.Embed(description="Setup has been sent. **Check your DM's**", color=msg.success_color)
        await ctx.send(embed=embed)


def setup(cog):
    cog.add_cog(CommandContextMenus(cog))
