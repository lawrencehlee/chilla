import random
import uuid
from datetime import date, datetime, timedelta
from typing import List, Tuple, Dict

from discord import User, Member

from includes.general import convert_keys_to_str
from models.draft_state import DraftState
from models.game import Game, GameStatus, EmptyGame, FinishedGame
from models.ingame_models import SwapResult, SwapError, ScrambleError
from models.profile import Outcome
from models.queue_models import Queue, UserInGame
from schemas import ingame_schema, member_schema, queue_schema, draft_schema
from services import map_service


def swap(user: User, target: Member) -> SwapResult:
    if not ingame_schema.is_ingame(user):
        return SwapResult.error(SwapError.USER_NOT_IN_GAME)

    if not ingame_schema.is_ingame(target):
        return SwapResult.error(SwapError.TARGET_NOT_IN_GAME)

    member_schema.check_profile(user)

    game_id = ingame_schema.get_game_id_from_user(user)
    ingame_schema.swap_players(user, target, game_id)
    game = game_data_to_game_model(ingame_schema.get_game(game_id))

    return SwapResult.success(game, user.name, target.name)


def get_games(queue: Queue = None) -> List[Game]:
    return [game_data_to_game_model(game_data) for game_data in ingame_schema.get_games(queue)]


def game_data_to_game_model(game_data) -> Game:
    game_id = game_data['gameId']
    game_queue = Queue(game_data['queue'])

    status = GameStatus(game_data["status"])
    unassigned = []
    team1 = []
    team2 = []

    for player in ingame_schema.get_all_ingame_players(game_id):
        if player["team"] is None:
            unassigned.append(UserInGame(player["userId"], player["username"], False))
        elif player["team"] == 1:
            team1.append(UserInGame(player["userId"], player["username"], player["isCaptain"], 1))
        elif player["team"] == 2:
            team2.append(UserInGame(player["userId"], player["username"], player["isCaptain"], 2))

    return Game(game_id, game_data.get('started'), game_queue,
                sort_players_by_name(team1), sort_players_by_name(team2), game_data.get("maps"),
                game_data.get("ended"), status, unassigned_players=sort_players_by_name(unassigned),
                reshuffles=game_data.get('reshuffles'))


def sort_players_by_name(players: List[UserInGame]):
    return sorted(players, key=lambda player: player.name)


def start_game(user: User, queue: Queue) -> Game:
    queue_schema.remove_from_other_queues(user, queue)
    game_id = generate_game_id()
    maps = map_service.get_maps(num_maps=1)
    ingame_schema.create_game(queue, game_id, maps)
    ingame_schema.generate_teams(queue, game_id)

    game_data = ingame_schema.get_game(game_id)

    return game_data_to_game_model(game_data)


def generate_game_id() -> str:
    return str(uuid.uuid4())


def start_draft_game(queue: Queue) -> Tuple[Game, DraftState]:
    game_id = generate_game_id()
    maps = map_service.get_maps(num_maps=2)
    draft_schema.generate_game(game_id, queue, maps)
    return get_game_and_draft_state(game_id)


def get_game_and_draft_state(game_id) -> Tuple[Game, DraftState]:
    return get(game_id), draft_schema.get_draft_state(game_id)


def shuffle_teams(game_id) -> Game:
    ingame_schema.shuffle_teams(game_id)
    return game_data_to_game_model(ingame_schema.get_game(game_id))


def get(game_id) -> Game:
    return game_data_to_game_model(ingame_schema.get_game(game_id))


def get_empty(game_id) -> EmptyGame:
    game_data = ingame_schema.get_game(game_id)
    game_queue = Queue(game_data['queue'])

    return EmptyGame(game_id, game_data['started'], game_queue, game_data.get("ended"),
                     GameStatus(game_data["status"]), game_data.get("maps"))


def query_empty(start_date: date, end_date: date) -> List[EmptyGame]:
    game_data = ingame_schema.query(start_date, end_date)
    return [EmptyGame(game['gameId'], game['started'], Queue(game['queue']), game.get("ended"),
                      GameStatus(game["status"]), game.get("maps")) for game in game_data]


def scramble_map(user, map_number) -> Tuple[List[str], ScrambleError]:
    """
    :param user:
    :param map_number: 1-indexed
    """
    if not ingame_schema.is_ingame(user):
        return None, ScrambleError.USER_NOT_IN_GAME

    game_id = ingame_schema.get_game_id_from_user(user)
    maps = get(game_id).maps
    if map_number > len(maps):
        return maps, ScrambleError.INVALID_MAP_NUMBER

    new_map = map_service.get_maps(1, set(maps))[0]

    maps[map_number - 1] = new_map
    ingame_schema.update_maps(game_id, maps)
    return maps, None


def calculate_delay_targets(user_ids):
    low = 15
    # high = 30
    # For every 100 games played, you get a modifier of -x seconds (rewards folks who play more)
    # modifier_base = -3
    # games_played_divisor = 100

    profiles = member_schema.query_profiles(user_ids)
    delay_targets = {}

    for profile in profiles:
        if profile['lastPlayed'] == 'Never':
            continue
        last_played = profile['lastPlayed']
        # games_played = profile['gamesPlayed']
        # modifier = int(modifier_base * games_played / games_played_divisor)
        # delay = random.randint(low, high) - modifier
        # delay = low if delay < low else delay
        delay = low
        delay_targets[profile['userId']] = last_played + timedelta(0, delay)

    return delay_targets


def finish(user, outcome: Outcome) -> EmptyGame:
    """
    :return: None if user is not in game
    """
    if not ingame_schema.is_ingame(user):
        return None

    game_id = ingame_schema.get_game_id_from_user(user)

    game = get(game_id)

    players_on_team, players_on_other_team = (game.team1_players, game.team2_players) if game.is_on_team1(user.id) \
        else (game.team2_players, game.team1_players)

    if outcome == Outcome.WIN:
        winner_ids = [player.user_id for player in players_on_team]
        loser_ids = [player.user_id for player in players_on_other_team]
        user_ids_to_outcome = {**{user_id: Outcome.WIN for user_id in winner_ids},
                               **{user_id: Outcome.LOSS for user_id in loser_ids}}
    elif outcome == Outcome.LOSS:
        winner_ids = [player.user_id for player in players_on_other_team]
        loser_ids = [player.user_id for player in players_on_team]
        user_ids_to_outcome = {**{user_id: Outcome.WIN for user_id in winner_ids},
                               **{user_id: Outcome.LOSS for user_id in loser_ids}}
    else:
        winner_ids = [player.user_id for player in players_on_team]
        loser_ids = [player.user_id for player in players_on_other_team]
        user_ids_to_outcome = {user_id: Outcome.TIE for user_id in winner_ids + loser_ids}

    ingame_schema.finish_game(game_id)
    member_schema.finish_game_for_users(game_id, user_ids_to_outcome)
    delay_targets = calculate_delay_targets(list(user_ids_to_outcome.keys()))
    member_schema.set_delay_targets(delay_targets)
    ingame_schema.update_rankings(winner_ids, loser_ids, outcome == Outcome.TIE)

    return get_empty(game_id)


def pick_player(drafting_user: User, user_ids: List[int]) -> Tuple[Game, DraftState]:
    game_id = ingame_schema.get_game_id_from_user(drafting_user)
    game, draft_state = get_game_and_draft_state(game_id)

    captain = [captain for captain in (game.team1_captain, game.team2_captain)
               if captain.user_id == drafting_user.id][0]

    if draft_state is None:
        raise ValueError("Drafting is already finished")
    if captain.team != draft_state.team_to_pick:
        raise ValueError("Wrong team to draft")
    if len(user_ids) != draft_state.num_picks:
        raise ValueError("Incorrect number of players to draft")

    draft_schema.pick_players(game_id, captain.team, user_ids)
    draft_schema.switch_pick_order(game_id, 2 if captain.team == 1 else 1,
                                   len(game.unassigned_players) - draft_state.num_picks)

    game, draft_state = get_game_and_draft_state(game_id)
    if len(game.unassigned_players) == 0:
        draft_schema.start_game(game_id)
        draft_schema.remove_draft_state(game_id)
        return get(game_id), draft_state

    return game, draft_state


def cancel_game(user: User) -> bool:
    # TODO: test and use in cog
    if not ingame_schema.is_ingame(user):
        return False

    game_id = ingame_schema.get_game_id_from_user(user)
    ingame_schema.delete(game_id)
    draft_schema.remove_draft_state(game_id)
    return True


def update_draft_state_messages(game_id, messages: Dict[int, int]):
    draft_schema.update_messages(game_id, convert_keys_to_str(messages))


def is_captain(user):
    game_id = ingame_schema.get_game_id_from_user(user)
    game = get(game_id)
    return user.id in (game.team1_captain.user_id, game.team2_captain.user_id)


def get_history() -> List[FinishedGame]:
    games = ingame_schema.get_recent_games(5)
    player_game_results = member_schema.query_player_game_results([game.game_id for game in games])
    finished_games = []

    for game in games:
        results = [result for result in player_game_results if result.game_id == game.game_id]
        tie = False
        winners = []
        losers = []
        for result in results:
            username = member_schema.get_profile_by_id(result.user_id)['username']
            if result.outcome == Outcome.TIE:
                tie = True
                winners.append(username)
            elif result.outcome == Outcome.WIN:
                winners.append(username)
            else:
                losers.append(username)

        finished_games.append(FinishedGame(game, winners, losers, tie, game.ended_at))

    return finished_games


def flip_results(game_id: str) -> bool:
    single_game_results = member_schema.query_player_game_results([game_id])
    if any([result.outcome == Outcome.TIE for result in single_game_results]):
        return False

    winner_ids = [result.user_id for result in single_game_results if result.outcome == Outcome.WIN]
    loser_ids = [result.user_id for result in single_game_results if result.outcome == Outcome.LOSS]

    member_schema.update_outcome_for_users(game_id, winner_ids, Outcome.LOSS)
    member_schema.update_outcome_for_users(game_id, loser_ids, Outcome.WIN)
    ingame_schema.update_rankings(loser_ids, winner_ids, False)

    return True


def pick_suggested_server(players):
    regions = []

    for player in players:
        player_region = member_schema.get_player_region(player.user_id)
        if player_region != "Not Set":
            regions.append(player_region)

    na_servers = ["Chicago PUG", "Los Angeles PUG"]
    eu_servers = ["London PUG"]
    aus_servers = ["Sydney PUG"]

    if not regions:
        return random.choice(na_servers)

    def popular(lst):
        return max(set(lst), key=lst.count)

    most_popular = popular(regions)

    if most_popular == "EU":
        return random.choice(eu_servers)
    elif most_popular == "AU":
        return random.choice(aus_servers)

    # Cheesy hack to pick Chicago in EU-friendly times and SLC in AU-friendly times
    now = datetime.now()
    if now.hour <= 3:
        return na_servers[0]
    return na_servers[1]


def update_game_server(game_id, server):
    ingame_schema.update_game_suggested_server(game_id, server)


def get_game_server(game_id):
    return ingame_schema.get_game_server(game_id)
