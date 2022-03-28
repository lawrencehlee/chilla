from datetime import datetime
from typing import Dict, List, Tuple

import discord
import timeago
from discord import Embed
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import create_button, create_actionrow, create_select_option, create_select

import config
from includes import custom_ids, logger, emojis
from models.draft_state import DraftState
from models.game import Game, GameStatus, FinishedGame
from models.leaderboards import Leaderboard
from models.queue_models import Queue
from schemas import member_schema
from services import game_service, map_service

success_color = 0x84ff00
error_color = 0xfc0303
accent_color = 0xebe534


async def error(ctx, msg):
    embed = discord.Embed(description=msg, color=error_color)
    await ctx.send(embed=embed)


async def success(ctx, msg, hidden=False):
    embed = discord.Embed(description=msg, color=success_color)
    await ctx.send(embed=embed, hidden=hidden)


async def refreshed_add(ctx, queue: str):
    await success(ctx, f"Refreshed add to **`{queue}`**.", hidden=True)


async def already_ingame(ctx):
    await ctx.send(f"You're already **ingame**.", hidden=True)


async def generating_teams(ctx, bot):
    embed = discord.Embed(description=f"{config.variables['live']} **Generating Teams** {config.variables['live']}")
    await send_in_correct_channel(ctx, bot, embed=embed)


async def added_to_queue(ctx, bot, queue: str, queue_count):
    user = ctx.author
    '''
    embed = discord.Embed(description=f"**{user.name}** added to **`{queue}`**", color=success_color)
    embed.set_author(icon_url=user.avatar_url, name=user.name)
    embed.set_footer(text=f"Server • {ctx.guild.name}")
    content = f"**`{queue} [{queue_count}/10]`**"
    await send_in_correct_channel(ctx, bot, content, embed)
    '''

    description = f"**{user.name}** added to **`{queue}`**"
    embed = discord.Embed(description=description, color=success_color)
    content = f"**`{queue} [{queue_count}/10]`**"
    await send_in_correct_channel(ctx, bot, content, embed)


async def added_to_queues(ctx, bot, queue_counts: Dict[str, int]):
    user = ctx.author
    embed = discord.Embed(description=f"**{user.name}** added to **`{', '.join(queue_counts.keys())}`**",
                          color=success_color)
    embed.set_author(icon_url=user.avatar_url, name=user.name)
    embed.set_author(icon_url=user.avatar_url, name=user.name)
    embed.set_footer(text=f"Server • {ctx.guild.name}")
    content = " ".join([f"**`{queue} [{count}/10]`**" for queue, count in queue_counts.items()])
    await send_in_correct_channel(ctx, bot, content, embed)


async def removed_from_single_queue(ctx, bot, queue, queue_count):
    user = ctx.author
    description = f"**{user.name}** removed from **`{queue}`**"
    embed = discord.Embed(description=description, color=error_color)
    content = f"**`{queue} [{queue_count}/10]`**"
    await send_in_correct_channel(ctx, bot, content, embed)


async def removed_from_all_queues(ctx, bot, queue_counts: Dict[str, int]):
    user = ctx.author
    description = f"**{user.name}** removed from **`all queues`**"
    embed = discord.Embed(description=description, color=error_color)
    content = ' '.join([f"**`{queue} [{count}/10]`**" for queue, count in queue_counts.items()])
    await send_in_correct_channel(ctx, bot, content, embed)


async def send_in_correct_channel(ctx, bot, content: str = None, embed: Embed = None, components=None):
    for guild in bot.guilds:
        if ctx.guild is None or ctx.guild.name != guild.name:
            channel = discord.utils.get(guild.text_channels, name=config.variables['channel'])
            if channel is not None:
                await channel.send(content=content, embed=embed, components=components)
        else:
            await ctx.send(content=content, embed=embed, components=components)


async def game_started_dm(bot, user_id):
    body = f"Hey there! Your game **has started**! Check the **`{config.variables['main_guild']}`** server for comms."
    embed = discord.Embed(description=body, color=success_color)

    try:
        player = await bot.fetch_user(user_id)
        await player.send(embed=embed)
    except:
        return


async def game_started(ctx, bot, game: Game):
    suggested_server = game_service.pick_suggested_server(game.get_all_players())
    game_service.update_game_server(game.game_id, suggested_server)
    buttons = [
        create_button(
            style=ButtonStyle.green,
            label="Shuffle Teams",
            custom_id=custom_ids.shuffle_teams
        ),
    ]
    maps = create_select(
        options=[
            create_select_option(map_name, value=map_name) for map_name in map_service.get_all_map_names_alphabetical()
        ],
        custom_id=custom_ids.map_choices,
        placeholder="Any captain, choose a map",
        min_values=1,
        max_values=1,
    )

    button_action_row = create_actionrow(*buttons)
    maps_action_row = create_actionrow(maps)
    maps = game.maps

    content = f"**`{str(game.queue.value).capitalize()} Game Started`**"

    body = f"""
        **`Maps:`** {', '.join(maps)}
        **`Suggested Server:`** {suggested_server}
    """
    embed = discord.Embed(title="Game Started", description=body, color=success_color)
    team1_captain = f"{config.variables['rank_red']} **`{str(member_schema.get_profile_by_id(game.team1_captain.user_id)['gamesPlayed'])}`** **`{game.team1_captain.name[:14]}`**"
    team2_captain = f"{config.variables['rank_red']} **`{str(member_schema.get_profile_by_id(game.team2_captain.user_id)['gamesPlayed'])}`** **`{game.team2_captain.name[:14]}`**"

    team1_players = []
    team2_players = []

    for player in game.team1_others:
        team1_players.append(
            f"{config.variables['rank']} **`{str(member_schema.get_profile_by_id(player.user_id)['gamesPlayed'])}`** **`{player.name[:14]}`**")
    for player in game.team2_others:
        team2_players.append(
            f"{config.variables['rank']} **`{str(member_schema.get_profile_by_id(player.user_id)['gamesPlayed'])}`** **`{player.name[:14]}`**")
    embed.add_field(name=f"{team1_captain}", value='\n'.join(team1_players))
    embed.add_field(name=f"{team2_captain}", value='\n'.join(team2_players))

    if maps[0].lower() in config.map_imgs:
        embed.set_thumbnail(url=config.map_imgs[maps[0].lower()])

    await send_in_correct_channel(ctx, bot, content=content, embed=embed,
                                  components=[button_action_row, maps_action_row])


async def display_chosen_map(ctx, game, old_map, _map):
    body = f"""
        A new map has been selected for **`{game['queue']}`**.
    """
    embed = discord.Embed(title="Map Changed", description=body)
    embed.add_field(name="**`Before`**", value=old_map)
    embed.add_field(name="**`After`**", value=_map)
    if _map.lower() in config.map_imgs:
        embed.set_thumbnail(url=config.map_imgs[_map.lower()])

    content = f"**`{ctx.author.name} chose a map`**"
    await ctx.send(embed=embed, content=content)


async def new_game_started(ctx, bot, game: Game, user):
    suggested_server = game_service.get_game_server(game.game_id)
    buttons = [
        create_button(
            style=ButtonStyle.green,
            label="Shuffle Teams",
            custom_id=custom_ids.shuffle_teams
        ),
    ]
    maps = create_select(
        options=[
            create_select_option(map_name, value=map_name) for map_name in map_service.get_all_map_names_alphabetical()
        ],
        custom_id=custom_ids.map_choices,
        placeholder="Any captain, choose a map",
        min_values=1,
        max_values=1,
    )

    button_action_row = create_actionrow(*buttons)
    maps_action_row = create_actionrow(maps)
    maps = game.maps

    body = f"""
        **`Maps:`** {', '.join(maps)}
        **`Suggested Server:`** {suggested_server}
    """
    embed = discord.Embed(title="Game Started", description=body, color=success_color)
    team1_captain = f"{config.variables['rank_red']} **`{str(member_schema.get_profile_by_id(game.team1_captain.user_id)['gamesPlayed'])}`** **`{game.team1_captain.name[:14]}`**"
    team2_captain = f"{config.variables['rank_red']} **`{str(member_schema.get_profile_by_id(game.team2_captain.user_id)['gamesPlayed'])}`** **`{game.team2_captain.name[:14]}`**"

    team1_players = []
    team2_players = []

    for player in game.team1_others:
        team1_players.append(
            f"{config.variables['rank']} **`{str(member_schema.get_profile_by_id(player.user_id)['gamesPlayed'])}`** **`{player.name[:14]}`**")
    for player in game.team2_others:
        team2_players.append(
            f"{config.variables['rank']} **`{str(member_schema.get_profile_by_id(player.user_id)['gamesPlayed'])}`** **`{player.name[:14]}`**")
    embed.add_field(name=f"{team1_captain}", value='\n'.join(team1_players))
    embed.add_field(name=f"{team2_captain}", value='\n'.join(team2_players))

    if maps[0].lower() in config.map_imgs:
        embed.set_thumbnail(url=config.map_imgs[maps[0].lower()])

    content = f"**`Reshuffled by {user.name}`**"
    await send_in_correct_channel(ctx, bot, content=content, embed=embed,
                                  components=[button_action_row, maps_action_row])


async def not_ingame(ctx):
    await ctx.send("You're not **in game**.", hidden=True)


async def other_not_ingame(ctx, name):
    await ctx.send(f"**{name}** isn't ingame.", hidden=True)


async def games_info(ctx, games: List[Game]):
    if len(games) == 0:
        await ctx.send(embed=(discord.Embed(description="No games at this time")))
        return

    bodies = []
    for game in games:
        if game.status == GameStatus.STARTED:
            bodies.append(f"""
                **{game.queue.value.upper()} GAME STARTED**
                
                **`Manatech (L):`** **{game.get_team1_captain_name()}**, {', '.join(game.get_team1_others_names())}
                **`Arcturus (R):`** **{game.get_team2_captain_name()}**, {', '.join(game.get_team2_others_names())}
                
                **`Maps:`** {', '.join(game.maps)}
                
                **`{timeago.format(game.started_at, datetime.now())}`**
                """)
        elif game.status == GameStatus.PENDING:
            bodies.append(f"""
                **{game.queue.value.upper()} GAME PENDING**

                **`Captains:`** {game.get_team1_captain_name()}, {game.get_team2_captain_name()}
                **`Players:`** {', '.join([player.name for player in game.unassigned_players])}
                """)

    embed = discord.Embed(description=("\n\n".join(bodies)), color=accent_color)
    await ctx.send(embed=embed)


async def swapped(ctx, bot, user_name, target_name):
    embed = discord.Embed(description=f"**{user_name}** swapped teams with **{target_name}**")
    await send_in_correct_channel(ctx, bot, embed=embed)


async def help_text(ctx):
    body = f"""
    **Queue**
    `/status`: Check the status of the selected queue(s)
    `/add`: Add yourself to the selected queue(s)
    `/del`: Remove yourself from the selected queue(s)
    
    **Game**
    `/games`: Check the status of the current games
    `/swap`: Swap teams with another player in your game
    `/sub`: Substitute a player in an existing game
    `/finish`: Mark your current game as complete
    
    **Meta**
    `/profile`: See a player's profile
    `/position`: Set your profile position
    `/bio`: Set your profile bio. Leaving it empty will remove it
    `/showstats`: Hide or show your profile stats
    `/leaderboard`: See the player leaderboard
    `/version`: See the bot version
    `/help`: You're looking at it
    
    **Admin-only**
    `/banplayer`: Ban a player because they're much better than you
    `/revokeban`: Realize that a player you previously banned isn't actually that much better than you
    `/purge`: Clear bot messages, allow all crime for 8 hours
    `/shutdown`: Murder the bot in cold blood, you monster
    """
    embed = discord.Embed(description=body, color=accent_color)
    await ctx.send(embed=embed, hidden=True)


async def maps_updated(ctx, maps):
    await success(ctx, f"Maps updated: {', '.join(maps)}")


async def show_updated_maps(ctx, maps, user, num_maps):
    if num_maps == 1:
        buttons = [
            create_actionrow(
                create_button(
                    style=ButtonStyle.green,
                    label="Shuffle Again",
                    custom_id="15529"
                )
            )
        ]
    elif num_maps == 2:
        buttons = [
            create_actionrow(
                create_button(
                    style=ButtonStyle.green,
                    label="Shuffle Map 1",
                    custom_id="15521"
                ),
                create_button(
                    style=ButtonStyle.green,
                    label="Shuffle Map 2",
                    custom_id="15522"
                )
            )
        ]
    embed = discord.Embed(title="Map Shuffled", description=f"**Map changed: \n`{', '.join(maps)}`**")
    if maps[0].lower() in config.map_imgs:
        embed.set_thumbnail(url=config.map_imgs[maps[0].lower()])
    await ctx.send(content=f"**`Reshuffled by {user.name}`**", embed=embed, components=buttons)


async def incorrect_map_number(ctx, maps):
    await ctx.send(f"Invalid map number: there are only {len(maps)} maps.", hidden=True)


async def game_finished(ctx, bot, queue: Queue, started_at: datetime, ended_at: datetime, outcome: str):
    game_time = timeago.format(started_at, ended_at)
    description = f"{queue.name} game has **finished**. Game time: **`{game_time.replace(' ago', '')}`**"

    embed = discord.Embed(title="Game Finished", description=description, color=accent_color)
    buttons = [
        create_button(
            style=ButtonStyle.green,
            label="Add again",
            custom_id=custom_ids.re_add
        )
    ]
    await send_in_correct_channel(ctx, bot, content=f"`{ctx.author.name}` finished with: `{outcome}`.", embed=embed,
                                  components=[create_actionrow(*buttons)])


async def drafting_started(ctx, bot, game: Game, draft_state: DraftState) -> Dict[int, int]:
    body = f"Captains: {game.get_team1_captain_name()}, {game.get_team2_captain_name()}"
    content = f"`Started drafting for {game.queue.value} game`"
    embed = discord.Embed(description=body, color=success_color)
    messages = await draft_info(bot, game, draft_state)
    await send_in_correct_channel(ctx, bot, content=content, embed=embed)
    return messages


async def draft_info(bot, game: Game, draft_state: DraftState) -> Dict[int, int]:
    select = create_select(
        options=[
            create_select_option(player.name, value=str(player.user_id)) for player in game.unassigned_players
        ],
        placeholder="Draft a player",
        min_values=draft_state.num_picks,
        max_values=draft_state.num_picks,
        custom_id=custom_ids.draft
    )
    buttons = [create_actionrow(select)]
    messages = {}

    for captain in game.team1_captain, game.team2_captain:
        try:
            user = await bot.fetch_user(captain.user_id)
        except Exception as e:
            logger.log(e)
            logger.log("Most likely, the error is due to testing with a non-real Discord user")
            continue

        body = f"""
            Please pick teams **fairly**.
            
            Available players: {', '.join([player.name for player in game.unassigned_players])}
            
            """

        team1 = []
        team2 = []
        captain1 = game.get_team1_captain_name()
        captain2 = game.get_team2_captain_name()
        for player in game.team1_players:
            if player.name != captain1:
                team1.append(player.name)
        for player in game.team2_players:
            if player.name != captain2:
                team2.append(player.name)

        body = body + f"\n"
        body = body + f"**`{captain1}:` {', '.join(team1)}**"
        body = body + "\n"
        body = body + f"**`{captain2}:` {', '.join(team2)}**"
        body = body + "\n\n"

        if draft_state.team_to_pick == captain.team:
            body = body + f"**Your pick!** You have `{draft_state.num_picks}` pick(s) remaining this round."
            components = buttons
        else:
            body = body + "**Waiting on opponent....**"
            components = None
        embed = discord.Embed(description=body, color=success_color)
        message = await user.send(embed=embed, components=components)
        messages[user.id] = message.id
    return messages


async def dm_game_has_started(game, captain):
    team1 = []
    team2 = []
    captain1 = game.get_team1_captain_name()
    captain2 = game.get_team2_captain_name()
    for player in game.team1_players:
        if player.name != captain1:
            team1.append(player.name)
    for player in game.team2_players:
        if player.name != captain2:
            team2.append(player.name)

    body = f"""
        **Teams:**
        **`{captain1}:`** {', '.join(team1)}
        **`{captain2}:`** {', '.join(team2)}
        
        **`Maps:`** {', '.join(game.maps)}
    """
    embed = discord.Embed(description=body, color=success_color)
    await captain.send(embed=embed)


async def show_comp_game_started(ctx, bot, game):
    '''
    buttons = [
        create_actionrow(
            create_button(
                style=ButtonStyle.blue,
                label="Shuffle Map 1",
                custom_id="15521"
            ),
            create_button(
                style=ButtonStyle.blue,
                label="Shuffle Map 2",
                custom_id="15522"
            )
        )
    ]
    '''
    team1 = []
    team2 = []
    captain1 = game.get_team1_captain_name()
    captain2 = game.get_team2_captain_name()
    for player in game.team1_players:
        if player.name != captain1:
            team1.append(player.name)
    for player in game.team2_players:
        if player.name != captain2:
            team2.append(player.name)

    body = f"""
        **Teams:**
        **`{captain1}:`** {', '.join(team1)}
        **`{captain2}:`** {', '.join(team2)}
        
        **`Maps:`** {', '.join(game.maps)}
    """
    embed = discord.Embed(description=body, color=success_color)

    await send_in_correct_channel(ctx, bot, content="**`Competitive game started`**", embed=embed)


async def captains_only(ctx):
    await ctx.send("This interaction is only available to captains.", hidden=True)


async def gs(ctx, bot):
    quickplay = [f"{config.variables['rank']} **210** **`-apo`**", f"{config.variables['rank']} **318** **`EGG`**",
                 f"{config.variables['rank']} **175** **`swingapples`**",
                 f"{config.variables['rank']} **224** **`MayorOfChicago`**"]
    competitive = [f"{config.variables['rank']} **2** **`Krayvok`**", f"{config.variables['rank']} **47** **`Sh4z`**"]
    newbloods = [f"{config.variables['rank']} **3** **`Player1`**", f"{config.variables['rank']} **8** **`Player2`**",
                 f"{config.variables['rank']} **15** **`Player3`**"]

    embed = discord.Embed(color=success_color)
    embed.add_field(name="QUICKPLAY **`[4/10]`**", value='\n'.join(quickplay))
    embed.add_field(name="COMPETITIVE **`[0/10]`**", value="**`10x FREE SLOTS`**")
    embed.add_field(name="NEWBLOODS **`[0/10]`**", value="**`10x FREE SLOTS`**")
    embed.add_field(name="TEST **`[0/10]`**", value="**`10x FREE SLOTS`**")

    await ctx.send(embed=embed)


async def show_leaderboard(ctx, leaderboard: Leaderboard):
    if leaderboard.start_date is None and leaderboard.end_date is None:
        title = "Leaderboard - All Time"
    else:
        start = leaderboard.start_date.strftime("%B %d, %Y")
        end = leaderboard.end_date.strftime("%B %d, %Y")
        title = f"Leaderboard - {start} to {end}"
    embed = discord.Embed(title=title)
    embed.add_field(name=f"{emojis.video_game} Most Games",
                    value=format_pairs_into_ranked_lines(leaderboard.most_games_played))
    embed.add_field(name=f"{emojis.trophy} Most Wins", value=format_pairs_into_ranked_lines(leaderboard.most_games_won))
    embed.add_field(name=f"{emojis.chart_with_upwards_trend} Highest Winrate*",
                    value=format_pairs_into_ranked_lines(leaderboard.highest_winrate))
    embed.add_field(name=f"{emojis.map_emoji} Most Popular Maps",
                    value=bold_mono(format_pairs_into_lines(leaderboard.most_popular_maps)))
    embed.add_field(name=f"{emojis.pencil} Total Games**", value=bold_mono(leaderboard.total_games))
    embed.add_field(name=f"{emojis.person_doing_cartwheel} Unique Players**",
                    value=bold_mono(leaderboard.unique_players))
    embed.set_footer(text="""* Excludes players with fewer than 5 total games in the time period.
** Excludes games and players prior to the "modern" Chilla era, i.e. when W/L/T tracking began.""")
    await ctx.send(embed=embed)


async def invalid_date(ctx):
    await ctx.send("Invalid date.", hidden=True)


def format_pairs_into_ranked_lines(pairs: List[Tuple]) -> str:
    if len(pairs) == 0:
        return "N/A"

    lines = []
    for i in range(len(pairs)):
        if i == 0:
            emoji = config.variables['gold']
        elif i == 1:
            emoji = config.variables['silver']
        elif i == 2:
            emoji = config.variables['bronze']
        else:
            emoji = config.variables['b_medal']

        value = pairs[i][1]
        value_text = f"{value:.2%}" if isinstance(value, float) else f"{value}"
        lines.append(f"{emoji} **`{pairs[i][0][:12]}: {value_text}`**")

    return "\n".join(lines)


def format_pairs_into_lines(pairs: List[Tuple], prefix=""):
    if len(pairs) == 0:
        return "N/A"
    return "\n".join([f"{prefix}{pair[0]}: {pair[1]}" for pair in pairs])


def bold_mono(text):
    return f"**`{text}`**"


async def cancel_game_message(ctx, user):
    embed = discord.Embed(title="Game Canceled", description=f"**{user.name}** has canceled the game",
                          color=error_color)
    await ctx.send(embed=embed)


async def force_remove_from_queue(ctx, admin, member):
    embed = discord.Embed(description=f"**{admin.name}** removed **{member}** from queue", color=accent_color)
    await ctx.send(embed=embed)


async def show_history(ctx, games: List[FinishedGame]):
    if len(games) == 0:
        description = "No recent games"
        embed = discord.Embed(title="Game History", description=description)
        await ctx.send(embed=embed)
        return

    description = "\n----------\n".join([f"""
    **{game.game.queue.value.upper()} Game on {", ".join(game.game.maps)}**
    Game ID: `{game.game.game_id}`
    `{timeago.format(game.ended_at, datetime.now())}`
    Tie: {game.tie}
    Winners: {", ".join(game.winners)}
    Losers: {", ".join(game.losers)}
    """ for game in games])

    select = create_select(
        options=[
            create_select_option(
                f"{game.game.queue.value.upper()} Game on {', '.join(game.game.maps)} ({game.game.game_id})",
                value=str(game.game.game_id)) for game in games if not game.tie
        ],
        placeholder="Reverse a game result (unavailable for ties)",
        min_values=1,
        max_values=1,
        custom_id=custom_ids.override
    )
    buttons = [create_actionrow(select)]

    embed = discord.Embed(title="Game History", description=description)
    await ctx.send(embed=embed, components=buttons)


async def result_flipped(ctx, game_id):
    embed = discord.Embed(description=f"Game result reversed for `{game_id}`")
    await ctx.send(embed=embed)


async def profile_setup(user, unique_id):
    regions = create_select(
        options=[
            create_select_option("NA", value="NA"),
            create_select_option("EU", value="EU"),
            create_select_option("AUS", value="AUS"),
        ],
        custom_id=unique_id,
        placeholder="Choose a region",
        min_values=1,
        max_values=1,
    )

    region_action_row = create_actionrow(regions)

    body = """
        Hi! Let's setup your profile.
        First, **select your region**. You have **2 minutes** before this message expires
    """
    embed = discord.Embed(title="Setup Profile", description=body, color=0xff00d4)

    try:
        await user.send(embed=embed, components=[region_action_row])
    except Exception as e:
        print(e)


async def stage1_profile_setup(ctx, id):
    positions = create_select(
        options=[
            create_select_option("Offense", value="Offense"),
            create_select_option("Chase", value="Chase"),
            create_select_option("Home Defense", value="Home Defense"),
            create_select_option("Flexible", value="Flexible"),
        ],
        custom_id=id,
        placeholder="Choose a position",
        min_values=1,
        max_values=1,
    )

    position_action_row = create_actionrow(positions)

    embed = discord.Embed(title="Set Position", description="Please choose your prefered **player position**",
                          color=0xff00d4)
    await ctx.send(embed=embed, components=[position_action_row])


async def stage2_profile_setup(ctx, id):
    show_stats = create_select(
        options=[
            create_select_option("Show Stats", value="Show"),
            create_select_option("Hide Stats", value="Hide"),
        ],
        custom_id=id,
        placeholder="Choose a selection",
        min_values=1,
        max_values=1,
    )

    show_stats_action_row = create_actionrow(show_stats)

    embed = discord.Embed(title="Show Stats",
                          description="You have the option to show stats. Choose a selection **below**", color=0xff00d4)
    await ctx.send(embed=embed, components=[show_stats_action_row])


async def complete_setup(ctx):
    body = """
        Profile setup is now complete! You can always update your settings by using the **`/setup`** command again
    """
    embed = discord.Embed(title="Setup Complete!", description=body, color=success_color)

    await ctx.send(embed=embed)


async def no_more_shuffles(ctx):
    await ctx.send("3 shuffles maximum. Try swapping?", hidden=True)


async def delayed_add(ctx, delay_seconds: int):
    description = f"Your game just finished; you can re-add in {delay_seconds} seconds"
    embed = discord.Embed(description=description, color=accent_color)
    await ctx.send(embed=embed, hidden=True)


async def expired(ctx):
    embed = discord.Embed(description="Expired :(", color=error_color)
    await ctx.send(embed=embed, hidden=True)
