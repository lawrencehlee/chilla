from pymongo import MongoClient

import config

client = MongoClient(host=config.variables["mongo_connection_string"])
db = client[config.variables["mongo_database_name"]]
