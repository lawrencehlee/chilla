import datetime
import random
from typing import List, Dict

from includes import mongo
from includes.general import convert_keys_to_int
from models.draft_state import BalancedPickOrder, DraftState
from models.game import GameStatus
from models.queue_models import Queue

pick_order = BalancedPickOrder()


def generate_game(game_id, queue: Queue, maps):
    players = list(mongo.db['Queue'].find({"queue": queue.value}).limit(10))
    mongo.db['Queue'].delete_many({"userId": {"$in": [player['userId'] for player in players]}})

    captain_ids = tuple(random.sample([player['userId'] for player in players], k=2))
    # For testing
    # captain_ids = (689277872694886566, 194611044902109184)

    player_data = [
        {
            "gameId": game_id,
            "userId": player["userId"],
            "username": player["username"],
            "isCaptain": player['userId'] in captain_ids,
            "team": captain_ids.index(player['userId']) + 1 if player['userId'] in captain_ids else None
        }
        for player in players
    ]
    mongo.db['Ingame'].insert_many(player_data)

    data = {
        "gameId": game_id,
        "queue": queue.value,
        "maps": maps,
        "status": 1,
        "started": None
    }
    mongo.db['GameData'].insert_one(data)

    draft_state = {
        "gameId": game_id,
        "teamToPick": 1,  # Always start picking on L team
        "numPicks": pick_order.num_picks(8),
        "messages": {}
    }
    mongo.db['DraftState'].insert_one(draft_state)


def get_draft_state(game_id) -> DraftState:
    draft_state_data = mongo.db['DraftState'].find_one({"gameId": game_id})
    if draft_state_data is None:
        return None
    return DraftState(draft_state_data['gameId'], draft_state_data['teamToPick'], draft_state_data['numPicks'],
                      convert_keys_to_int(draft_state_data['messages']))


def pick_players(game_id, team: int, player_ids: List[int]):
    data = {
        "$set": {
            "team": team
        }
    }

    mongo.db['Ingame'].update_many({"gameId": game_id, "userId": {"$in": player_ids}}, data)


def switch_pick_order(game_id, team: int, num_players_left: int):
    data = {
        "$set": {
            "teamToPick": team,
            "numPicks": pick_order.num_picks(num_players_left)
        }
    }

    mongo.db["DraftState"].update_one({"gameId": game_id}, data)


def get_captain_message_id(game_id, user):
    data = {
        "gameId": game_id,
        f"messageIds.{user.id}": {"$exists": True}
    }

    return mongo.db['GameData'].find_one(data)['messageIds'][str(user.id)]['msgId']


def start_game(game_id):
    mongo.db["GameData"].update_one(
        {"gameId": game_id},
        {"$set": {
            "status": GameStatus.STARTED.value,
            "started": datetime.datetime.now()
        }})


def remove_draft_state(game_id):
    mongo.db["DraftState"].delete_one({"gameId": game_id})


def update_messages(game_id, messages: Dict[str, int]):
    mongo.db['DraftState'].update_one({"gameId": game_id}, {"$set": {"messages": messages}})
