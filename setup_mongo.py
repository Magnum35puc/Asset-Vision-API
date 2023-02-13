import Configuration

from pymongo import MongoClient, ASCENDING, errors
from datetime import datetime, timedelta

client = MongoClient(Configuration.mongoDB_str)
db = client.AssetVision
assets = db.assets
portfolios = db.portfolios

db.assets.create_index([("symbol", ASCENDING)],unique=True)