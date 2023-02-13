import Configuration

from pymongo import MongoClient, ASCENDING, errors
from datetime import datetime, timedelta

client = MongoClient(Configuration.mongoDB_str)
db = client.AssetVision
assets = db.assets
portfolios = db.portfolios

#db.assets.create_index([("symbol", ASCENDING)],unique=True)


for portfolio in portfolios.find():
    print(portfolio)
    asset_symbols = assets.find({"portfolio_id": portfolio["_id"]}).distinct("symbol")
    portfolio_assets = []
    for symbol in asset_symbols:
        asset = assets.find_one({"symbol": symbol})
        portfolio_assets.append(asset)
    print(portfolio_assets)