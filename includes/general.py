from typing import Dict

from discord_slash.context import SlashContext

import config
from schemas import member_schema


async def correct_channel(ctx: SlashContext, user):
    channel = ctx.channel.name
    if member_schema.is_banned(user):
        await ctx.send("You are currently banned.", hidden=True)
        return False
    if channel != config.variables['channel']:
        await ctx.send(f"Incorrect channel. Use **`#{config.variables['channel']}`** instead.", hidden=True)
        return False
    return True

async def admin_channel(ctx: SlashContext, user):
    channel = ctx.channel.name
    if member_schema.is_banned(user):
        await ctx.send("You are currently banned.", hidden=True)
        return False
    if channel != config.variables['admin_channel']:
        await ctx.send(f"Incorrect channel. Use **`#{config.variables['admin_channel']}`** instead.", hidden=True)
        return False
    return True


def verify_channel(func):
    """
    TODO: this doesn't work with other args
    Decorator that automatically verifies the slash command is being called from the right channel.
    Needs to be AFTER the slash decorator.
    Cannot be used on functions with kwargs!
    """

    async def wrapper(*args):
        if len(args) < 2:
            raise ValueError("No ctx argument passed to decorated function")

        ctx = args[1]
        if not await correct_channel(ctx, ctx.author):
            return

        return await func(*args)

    return wrapper


def convert_keys_to_int(dictionary: Dict[str, int]) -> Dict[int, int]:
    return {int(key): value for key, value in dictionary.items()}


def convert_keys_to_str(dictionary: Dict[int, int]) -> Dict[str, int]:
    return {str(key): value for key, value in dictionary.items()}