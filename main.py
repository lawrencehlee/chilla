import datetime
import threading
from glob import glob

import discord
from discord.ext import commands, tasks
from discord_slash import SlashCommand
from simple_http_server import server, request_map

import config
from schemas import queue_schema, general_schema

COGS = [path.split("/")[-1][:-3] for path in glob("./cogs/*.py")]
if config.variables['environment'] == "PROD":
    COGS.remove("testing")

client = commands.Bot(command_prefix="!")
slash = SlashCommand(client, sync_commands=True)


@tasks.loop(seconds=5)
async def autoremove():
    result = queue_schema.get_all_queue_players()
    for player in result:
        added = player['added']
        if added < datetime.datetime.now() - datetime.timedelta(minutes=config.variables['auto_remove']):
            queue_schema.auto_remove_from_queue(player['userId'])
            for guild in client.guilds:
                channel = discord.utils.get(guild.text_channels, name=config.variables['channel'])
                embed = discord.Embed(
                    description=f"Removed **{player['username']}** from **`{player['queue']}`** after **{config.variables['auto_remove']}** minutes",
                    color=0xfc0303)
                if channel is not None:
                    await channel.send(embed=embed, content=f"<@!{player['userId']}>")


@tasks.loop(seconds=5)
async def autoremove_expired_messages():
    messages = general_schema.get_all_setup_messages()
    for message in messages:
        if message['created'] < datetime.datetime.now() - datetime.timedelta(
                minutes=config.variables['expire_message']):
            embed = discord.Embed(description="Profile setup has expired. Use **`/setup`** again to restart")
            user = await client.fetch_user(message['userId'])
            await user.send(embed=embed)
            general_schema.remove_setup(message['uniqueueId'])


@client.event
async def on_ready():
    print(f"CHILLA ONLINE | VERSION: {config.variables['version']}")
    await client.change_presence(activity=discord.Game(name="MA:CE"))
    autoremove.start()
    autoremove_expired_messages.start()


@request_map("/")
def healthcheck():
    return {"status": "All good!"}


def run_bot():
    for cog in COGS:
        client.load_extension(f"cogs.{cog}")
    '''
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{filename[:-3]}')
    '''
    client.run(config.variables['token'])


def run_server():
    server.start(port=8080)


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    run_bot()
