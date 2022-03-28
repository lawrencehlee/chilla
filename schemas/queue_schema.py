import datetime
from typing import Dict

from includes import mongo
from models.queue_models import Queue


def add_to_queue(user, queue: Queue):
    queues = [q.name for q in Queue] if queue == "all" else [queue.value]
    for q in queues:
        data = {
            "userId": user.id,
            "username": user.name,
            "queue": q,
            "added": datetime.datetime.now()
        }
        mongo.db['Queue'].insert_one(data)


def refresh_add(user, queue: Queue):
    queues = [q.name for q in Queue] if queue == "all" else [queue.value]
    for q in queues:
        data = {"$set": {"added": datetime.datetime.now()}}
        mongo.db['Queue'].update_one({"userId": user.id, "queue": q}, data)


def remove_from_queue(user, queue):
    if queue == "all":
        mongo.db['Queue'].delete_many({"userId": user.id})
    else:
        mongo.db['Queue'].delete_one({"userId": user.id, "queue": queue})


def get_queue_count(queue: Queue):
    return mongo.db['Queue'].count_documents({"queue": queue.value})


def get_queue_players(queue):
    return mongo.db['Queue'].find({"queue": queue})


def check_if_in_queue(user, queue: Queue):
    if mongo.db['Queue'].find_one({"userId": user.id, "queue": queue.value}):
        return True
    else:
        return False


def get_all_queue_counts() -> Dict[str, int]:
    queues = ["quickplay", "newbloods", "test"]
    return {queue: mongo.db['Queue'].count_documents({"queue": queue}) for queue in queues}


def queue_is_ingame(queue):
    data = {
        "queue": queue,
        "$or": [
            {
                "status": 1
            },
            {
                "status": 2
            }
        ]
    }
    if mongo.db['GameData'].count_documents(data) > 0:
        return True
    else:
        return False


def comp_queue_is_ingame(queue):
    if mongo.db['GameData'].count_documents({"queue": queue, "status": 2}) > 0:
        return True
    else:
        return False


def get_ingame_queue_game_data(queue):
    return mongo.db['GameData'].find({"queue": queue, "status": 2})


def get_all_queue_players():
    return mongo.db['Queue'].find({})


def auto_remove_from_queue(user_id):
    mongo.db['Queue'].delete_one({"userId": user_id})


def remove_from_other_queues(user, queue: Queue):
    mongo.db['Queue'].delete_many({"userId": user.id, "queue": {"$ne": queue.value}})
