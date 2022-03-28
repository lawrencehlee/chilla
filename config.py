from os import getenv
from typing import List

from dotenv import load_dotenv

load_dotenv()


def getenv_int(key) -> int:
    value = getenv(key)
    return None if value is None else int(value)


def getenv_list_int(key) -> List[int]:
    value = getenv(key)
    if value is None:
        return []
    return [int(value.strip()) for value in value.split(",")]


variables = {
    "environment": getenv("CHILLA_ENVIRONMENT", "DEV"),
    "mongo_connection_string": getenv("CHILLA_MONGO_CONNECTION_STRING"),
    "mongo_database_name": getenv("CHILLA_MONGO_DATABASE_NAME", "Chilla"),
    "token": getenv("CHILLA_DISCORD_TOKEN"),
    "version": "3.5.0",
    "main_guild": getenv("CHILLA_DISCORD_MAIN_GUILD"),
    "main_guild_id": getenv_int("CHILLA_DISCORD_MAIN_GUILD_ID"),
    "channel": getenv("CHILLA_DISCORD_CHANNEL"),
    "channelid": getenv_int("CHILLA_DISCORD_CHANNEL_ID"),
    "guild_ids": getenv_list_int("CHILLA_DISCORD_GUILD_IDS"),
    "admin_channel": getenv("CHILLA_DISCORD_ADMIN_CHANNEL"),
    "avail": "<:av:890348480277659649>",
    "taken": "<:ta:890348480881655868>",
    "live": "<a:live2:867115966278402128>",
    "notlive": "<:notlive:845432882314215464>",
    "gold": "<:gold:922551402964852856>",
    "silver": "<:silver:922548735504945202>",
    "bronze": "<:bronze:922548574741467147>",
    "b_medal": "<:b_medal:922550453772894278>",
    "auto_remove": 45,
    "expire_message": 2,
    "twitch_client_id": getenv("TWITCH_CLIENT_ID"),
    "twitch_client_secret": getenv("TWITCH_CLIENT_SECRET"),
    "twitch_game_id": 517069,
    "chillin_role": 756357850003144705,
    "chilla_admin_role": 894630221607755826,
    "chilla_sa_role": 894980304631115896,
    "rank": "<:rank2:937024794610790471>",
    "rank_red": "<:rank_red:937036271421907068>"
}

map_imgs = {
    "exhumed": "https://i.imgur.com/MQGW6eJ.jpg",
    "elite": "https://i.imgur.com/9Xib6tF.jpg",
    "brynhildr": "https://i.imgur.com/9CAybAC.jpg",
    "minora": "https://i.imgur.com/YMetT8z.jpg",
    "ingonyama": "https://i.imgur.com/MRbwf5u.jpg",
    "twilightgrove": "https://i.imgur.com/GTzvA8t.jpg",
    "kryosis": "https://i.imgur.com/HJuawtp.jpg",
    "nightflare": "https://i.imgur.com/8wMHNjK.jpg",
    "outpost": "https://i.imgur.com/Nkc04Di.jpg",
    "forlorn": "https://i.imgur.com/igFANQB.png",
    "relay": "https://i.imgur.com/jQnPNBh.png",
    "sunward": "https://i.imgur.com/aIr4rjt.png",
    "yolandi": "https://i.imgur.com/WwkEDgj.png",
}


def queues(default: bool):
    if default is True:
        return [{"name": "Quickplay", "value": "quickplay"},
                {"name": "Newbloods", "value": "newbloods"},
                {"name": "Test", "value": "test"}]

    return [{"name": "All Queues", "value": "all"},
            {"name": "Quickplay", "value": "quickplay"},
            {"name": "Newbloods", "value": "newbloods"},
            {"name": "Test", "value": "test"}]
