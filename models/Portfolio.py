from typing import List
from models.Asset import Asset
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from pydantic import BaseModel
from utils.secret_tools import access_secret_version


from pymongo import MongoClient
from main import access_secret_version

client = MongoClient(access_secret_version("mongodb_str"))
db = client.AssetVision
assets_db = db.assets


class Portfolio(BaseModel):
    owner : str = None
    name: str = None
    portfolio_content: dict = {}
    created_at: datetime = None
    last_updated_at: datetime = datetime.now()

    def __str__(self):
        return f"{self.name} ({self.owner})"

  
""" 
asset_details = {"symbol": "ETH","name": "Ethereum","price": 1540,"currency": "USD","asset_class": "Cryptocurrency","industry": "Blockchain","marketplace": None,"user" : "TPUISE"}
asset = Asset(**asset_details)
p = Portfolio(owner = "12", name = "123", assets = [asset, asset])
print(p)
 """


