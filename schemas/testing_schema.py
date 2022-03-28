import datetime

from trueskill import Rating

from includes import mongo


def add_test_players(queue, amount):
    rating = Rating()
    for x in range(amount):
        data = {
            "userId": x + 1,
            "username": f"Player{x + 1}",
            "gamesPlayed": 0,
            "position": "Offence",
            "lastPlayed": "Never",
            "region": "Not Set"
        }
        mongo.db['Profiles'].insert_one(data)
        data = {
            "userId": x + 1,
            "username": f"Player{x + 1}",
            "rank": rating.mu,
            "confidence": rating.sigma
        }
        mongo.db['Ranks'].insert_one(data)
        data = {
            "userId": x + 1,
            "username": f"Player{x + 1}",
            "queue": queue,
            "added": datetime.datetime.now()
        }
        mongo.db['Queue'].insert_one(data)


def reset_everything():
    mongo.db['Queue'].delete_many({})
    mongo.db['Players'].delete_many({})
    mongo.db['Profiles'].delete_many({})
    mongo.db['Ranks'].delete_many({})
    mongo.db['Banned'].delete_many({})
    mongo.db['GameData'].delete_many({})
    mongo.db['Ingame'].delete_many({})
    mongo.db['PlayerData'].delete_many({})
    mongo.db['Warnings'].delete_many({})
    mongo.db['DraftState'].delete_many({})
    mongo.db['Messages'].delete_many({})


def force_captain(user_id):
    team = mongo.db['Ingame'].find_one({"userId": user_id})['team']
    mongo.db['Ingame'].update_one({"team": team, "isCaptain": True}, {
        "$set": {
            "isCaptain": False
        }
    })
    mongo.db['Ingame'].update_one({"userId": user_id}, {
        "$set": {
            "isCaptain": True
        }
    })
