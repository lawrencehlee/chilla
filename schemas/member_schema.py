from datetime import datetime
from typing import Tuple, Dict, List

from discord import User
from pymongo import UpdateOne
from trueskill import Rating

from includes import mongo
from models.profile import Outcome, PlayerGameResult


def check_profile(user: User):
    rating = Rating()
    profile = get_profile(user)
    rank = get_player_rank(user)
    if profile is None:
        data = {
            "userId": user.id,
            "username": user.name,
            "gamesPlayed": 0,
            "position": "Offence",
            "lastPlayed": "Never",
            "hideRank": True,
            "region": "Not Set",
            "delayTarget": datetime.min
        }
        mongo.db['Profiles'].insert_one(data)
        data = {
            "userId": user.id,
            "username": user.name,
            "rank": rating.mu,
            "confidence": rating.sigma
        }
        mongo.db['Ranks'].insert_one(data)
        return
    if user.name != profile['username']:
        mongo.db['Profiles'].update_one(
            {"userId": user.id},
            {"$set": {"username": user.name}})
    if user.name != rank['username']:
        mongo.db['Ranks'].update_one(
            {"userId": user.id},
            {"$set": {"username": user.name}})


def get_profile(user):
    return mongo.db['Profiles'].find_one({"userId": user.id})


def get_player_region(user_id):
    return mongo.db['Profiles'].find_one({"userId": user_id})['region']


def get_profile_by_id(user_id):
    return mongo.db['Profiles'].find_one({"userId": user_id})


def query_user_ids_who_have_played_in_games(game_ids) -> List[int]:
    return mongo.db['PlayerData'].distinct("userId", {"gameId": {"$in": game_ids}})


def is_banned(user):
    if mongo.db['Banned'].count_documents({"userId": user.id}) > 0:
        return True
    else:
        return False


def already_admin(member):
    if mongo.db['Admins'].count_documents({"userId": member.id}) > 0:
        return True
    else:
        return False


def add_admin(member):
    mongo.db['Admins'].insert_one({"userId": member.id, "username": member.name})


def remove_admin(member):
    mongo.db['Admins'].delete_one({"userId": member.id})


def is_banned(member):
    if mongo.db['Banned'].count_documents({"userId": member.id}) > 0:
        return True
    else:
        return False


def ban_player(admin, member):
    mongo.db['Banned'].insert_one(
        {"userId": member.id, "username": member.name, "issued": datetime.now(), "by": admin.name})
    mongo.db['Warnings'].delete_many({"userId": member.id})


def unban_player(member):
    mongo.db['Banned'].delete_one({"userId": member.id})


def get_top_players():
    result = mongo.db['Profiles'].find({}).sort("gamesPlayed", -1).limit(10)
    return result


def get_admins():
    return mongo.db['Admins'].find({}).limit(10)


def get_total_players():
    return mongo.db['Profiles'].count_documents({})


def get_total_games():
    return mongo.db['GameData'].count_documents({})


def update_player_position(user, position):
    if position == "offense":
        mongo.db['Profiles'].update_one({"userId": user.id}, {"$set": {"position": "Offense"}})
    elif position == "homed":
        mongo.db['Profiles'].update_one({"userId": user.id}, {"$set": {"position": "Home D"}})
    elif position == "chase":
        mongo.db['Profiles'].update_one({"userId": user.id}, {"$set": {"position": "Chase"}})
    elif position == "flexible":
        mongo.db['Profiles'].update_one({"userId": user.id}, {"$set": {"position": "Flexible"}})


def get_player_rank(user):
    return mongo.db['Ranks'].find_one({"userId": user.id})


def get_player_rank_by_id(user_id):
    return mongo.db['Ranks'].find_one({"userId": user_id})


def change_rank_visibility(user, option: bool):
    data = {
        "$set": {
            "hideRank": option
        }
    }

    print(option)
    try:
        mongo.db['Profiles'].update_one({"userId": user.id}, data)
    except Exception as e:
        print(e)


def update_profile_bio(user, bio):
    mongo.db['Profiles'].update_one({"userId": user.id}, {"$set": {"bio": bio}})


def finish_game_for_users(game_id, user_ids_to_outcome: Dict[int, Outcome]):
    mongo.db['Profiles'].update_many(
        {"userId": {"$in": (list(user_ids_to_outcome.keys()))}},
        {
            "$inc": {"gamesPlayed": 1},
            "$set": {"lastPlayed": datetime.now()}
        })
    mongo.db["PlayerData"].insert_many(
        {
            "userId": user_id,
            "gameId": game_id,
            "outcome": outcome.value
        } for user_id, outcome in user_ids_to_outcome.items())


def set_delay_targets(delay_targets: Dict[int, datetime]):
    mongo.db['Profiles'].bulk_write(
        [UpdateOne({"userId": user_id}, {"$set": {"delayTarget": target}}) for user_id, target in delay_targets.items()]
    )


def update_outcome_for_users(game_id, user_ids, outcome: Outcome):
    mongo.db["PlayerData"].update_many(
        {
            "userId": {"$in": user_ids},
            "gameId": game_id,
        },
        {
            "$set": {
                "outcome": outcome.value
            }
        })


def get_player_stats(user_id) -> Tuple[int, int, int]:
    """
    :param user_id:
    :return: Tuple of wins, losses, and ties
    """
    wins = mongo.db["PlayerData"].count_documents({"userId": user_id, "outcome": Outcome.WIN.value})
    losses = mongo.db["PlayerData"].count_documents({"userId": user_id, "outcome": Outcome.LOSS.value})
    ties = mongo.db["PlayerData"].count_documents({"userId": user_id, "outcome": Outcome.TIE.value})
    return wins, losses, ties


def query_player_game_results(game_ids: List[str]) -> List[PlayerGameResult]:
    results_for_game = mongo.db["PlayerData"].find({"gameId": {"$in": game_ids}})
    return [PlayerGameResult(result["userId"], result["gameId"], Outcome(result["outcome"])) for result
            in results_for_game]


def get_number_of_warnings(user):
    return mongo.db['Warnings'].count_documents({"userId": user.id})


def warn_player(admin, user):
    mongo.db['Warnings'].insert_one(
        {"userId": user.id, "username": user.name, "issued": datetime.now(), "by": admin.name})


def remove_warnings(user):
    mongo.db['Warnings'].delete_many({"userId": user.id})


def remove_single_warnings(user, userwarnings, amount):
    warnings = userwarnings - amount
    for x in range(amount):
        mongo.db['Warnings'].delete_one({"userId": user.id})
    new_warning_amount = get_number_of_warnings(user)

    return new_warning_amount


def get_all_banned():
    return mongo.db['Banned'].find({})


def get_all_warned():
    return mongo.db['Warnings'].find({})


def update_member_region(user, region):
    data = {
        "$set": {
            "region": region
        }
    }

    mongo.db['Profiles'].update_one({"userId": user.id}, data)


def update_player_position_new(user, position):
    data = {
        "$set": {
            "position": position
        }
    }

    mongo.db['Profiles'].update_one({"userId": user.id}, data)


def update_stats_visibility(user, visible):
    data = {
        "$set": {
            "hideRank": True if visible == "Hide" else False
        }
    }

    mongo.db['Profiles'].update_one({"userId": user.id}, data)


def query_profiles(user_ids):
    return mongo.db['Profiles'].find({"userId": {"$in": user_ids}})
