from includes import mongo
import datetime

def check_setup_exists(user):
    if mongo.db['Messages'].find({"userId":user.id}).count() < 1:
        return False
    return True

def add_profile_setup(user, uniqueue_id, stage):
    data = {
        "userId":user.id,
        "uniqueueId":uniqueue_id,
        "created":datetime.datetime.now(),
        "stage":stage
    }

    mongo.db['Messages'].insert_one(data)

def check_custom_id_exists(id):
    if mongo.db['Messages'].find_one({"uniqueueId":id}):
        return True
    return False

def get_message_stage(id):
    return mongo.db['Messages'].find_one({"uniqueueId":id})['stage']

def update_stage(id, user, stage):
    data = {
        "$set": {
            "stage":stage
        }
    }

    mongo.db['Messages'].update_one({"uniqueueId":id, "userId":user.id}, data)

def remove_setup(id):
    mongo.db['Messages'].delete_one({"uniqueueId":id})

def get_all_setup_messages():
    return mongo.db['Messages'].find({})