import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option

import config
from includes import msg
from includes.general import correct_channel
from models import twitch
from services import analytics_service

twitch_streams = twitch.TwitchStreams(config.variables['twitch_client_id'], config.variables['twitch_client_secret'],
                                      config.variables['twitch_game_id'])


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Misc Cog: Loaded")

    @cog_ext.cog_slash(
        name="leaderboard",
        description="Shows player leaderboard",
        guild_ids=config.variables['guild_ids'],
        options=[
            create_option(
                name="month",
                description="Pick a month",
                required=False,
                option_type=4,
                choices=[num for num in range(1, 13)]
            ),
            create_option(
                name="year",
                description="Pick a year",
                required=False,
                option_type=4,
                choices=[2022, 2021]
            )
        ],
    )
    async def _leaderboard(self, ctx: SlashContext, month=None, year=None):
        if not await correct_channel(ctx, ctx.author):
            return

        await ctx.defer()
        leaderboard = analytics_service.get_leaderboard(year, month)
        if leaderboard is None:
            await msg.invalid_date(ctx)
            return
        await msg.show_leaderboard(ctx, leaderboard)

    @cog_ext.cog_slash(
        name="version",
        description="Shows the bot version",
        guild_ids=config.variables['guild_ids']
    )
    async def _version(self, ctx: SlashContext):
        if not await correct_channel(ctx, ctx.author):
            return

        embed = discord.Embed(description=f"Chilla Version: **`{config.variables['version']}`**")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="help",
        description="Shows help information for bot commands",
        guild_ids=config.variables['guild_ids']
    )
    async def _help(self, ctx: SlashContext):
        if not await correct_channel(ctx, ctx.author):
            return

        await msg.help_text(ctx)

    @cog_ext.cog_slash(
        name="streams",
        description="Show current streams",
        guild_ids=config.variables['guild_ids']
    )
    async def _streams(self, ctx: SlashContext):
        await ctx.defer()
        try:
            streams = twitch_streams.get_streams()
        except Exception as e:
            print(e)
        if 'data' in streams and streams['data']:
            embed = discord.Embed(color=msg.accent_color)
            for stream in streams['data']:
                embed.add_field(
                    name=f"{stream['viewer_count']} <:views:887829020719333407> {stream['user_name']} - {stream['title']}",
                    value=f"[twitch.tv/{stream['user_name']}](https://twitch.tv/{stream['user_name']})", inline=False)
        else:
            embed = discord.Embed(description="No streams for **Midair 2**", color=msg.accent_color)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Misc(bot))
