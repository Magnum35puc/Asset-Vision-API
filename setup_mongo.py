from pymongo import MongoClient, ASCENDING, errors
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from utils.secret_tools import access_secret_version

client = MongoClient(access_secret_version("mongodb_str"))
db = client.AssetVision
assets = db.assets
portfolios = db.portfolios
users = db.users

assets.create_index([("symbol", ASCENDING)],unique=True)
users.create_index([("username", ASCENDING)],unique=True)
portfolios.create_index([("owner", ASCENDING),("name", ASCENDING)], unique=True)
